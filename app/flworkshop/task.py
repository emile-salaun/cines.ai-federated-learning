"""flworkshop: model, training and evaluation (no federated logic here)."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):
    """Simple CNN (adapted from 'PyTorch: A 60 Minute Blitz').

    Works for 3×32×32 (CIFAR-10) and 1×28×28 (Fashion-MNIST) inputs.
    """

    def __init__(self, in_channels: int = 3, img_size: int = 32, num_classes: int = 10):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        side = ((img_size - 4) // 2 - 4) // 2  # two conv5 + pool2 blocks
        self.flat = 16 * side * side
        self.fc1 = nn.Linear(self.flat, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.reshape(-1, self.flat)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


def build_model(shape: tuple[int, int, int]) -> Net:
    channels, height, _ = shape
    return Net(in_channels=channels, img_size=height)


def _prepare(images: torch.Tensor) -> torch.Tensor:
    """uint8 [0, 255] -> float [-1, 1]. Done per batch to keep memory low."""
    return images.float().div_(255.0).sub_(0.5).div_(0.5)


def train(net, trainloader, epochs, lr, device, proximal_mu: float = 0.0):
    """Train the model on the training set; return the mean loss.

    ``proximal_mu > 0`` adds the FedProx proximal term (mu/2)·||w - w_global||².
    """
    net.to(device)
    global_params = [p.detach().clone() for p in net.parameters()] if proximal_mu > 0 else None
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(net.parameters(), lr=lr, momentum=0.9)
    net.train()
    running_loss, steps = 0.0, 0
    for _ in range(epochs):
        for images, labels in trainloader:
            images, labels = _prepare(images).to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(net(images), labels)
            if global_params is not None:
                prox = sum(
                    (p - g).pow(2).sum() for p, g in zip(net.parameters(), global_params)
                )
                loss = loss + (proximal_mu / 2) * prox
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            steps += 1
    return running_loss / max(steps, 1)


def test(net, testloader, device):
    """Evaluate the model; return (loss, accuracy)."""
    net.to(device)
    criterion = nn.CrossEntropyLoss(reduction="sum")
    net.eval()
    correct, loss, total = 0, 0.0, 0
    with torch.no_grad():
        for images, labels in testloader:
            images, labels = _prepare(images).to(device), labels.to(device)
            outputs = net(images)
            loss += criterion(outputs, labels).item()
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.numel()
    return loss / max(total, 1), correct / max(total, 1)


def test_per_class(net, testloader, device, num_classes: int = 10):
    """Evaluate the model; return (loss, accuracy, per-class accuracy list)."""
    net.to(device)
    criterion = nn.CrossEntropyLoss(reduction="sum")
    net.eval()
    correct = torch.zeros(num_classes)
    count = torch.zeros(num_classes)
    loss = 0.0
    with torch.no_grad():
        for images, labels in testloader:
            images, labels = _prepare(images).to(device), labels.to(device)
            outputs = net(images)
            loss += criterion(outputs, labels).item()
            hit = (outputs.argmax(1) == labels).float().cpu()
            count += torch.bincount(labels.cpu(), minlength=num_classes).float()
            correct += torch.bincount(labels.cpu(), weights=hit, minlength=num_classes)
    total = count.sum().item()
    per_class = (correct / count.clamp(min=1)).tolist()
    return loss / max(total, 1), correct.sum().item() / max(total, 1), per_class
