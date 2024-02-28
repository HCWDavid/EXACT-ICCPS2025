import math
import os
from methods import Segmenter
from matplotlib import pyplot as plt
import torch
from utilities import printc
from utils_loader import get_dataloaders
from torch.optim.lr_scheduler import ReduceLROnPlateau

from utils_metrics import mean_iou

def main():
    config = {
        
        'batch_size': 128,
        'epochs':100,
        'fsl': False
    }
    
    train_loader, val_loader, test_loader = get_dataloaders(config)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Segmenter(embed_dims=256, num_classes=5).float().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=10, verbose=True, threshold=0.0001, threshold_mode='rel', cooldown=0, min_lr=0, eps=1e-08)

    
    criterion = torch.nn.CrossEntropyLoss()
    
    # Iterate over the training data
    logs = {}
    # change the plt size:
    best_loss = math.inf
    counter_i = 0
    for epoch in range(config['epochs']):
        for images, labels in train_loader:
            b, h, c = images.shape
            # Forward pass
            images = images.float().to(device)
            labels = labels.to(device)
            outputs = model(images)
            outputs = outputs.transpose(1, 2)
            # printc(outputs.shape, labels.shape)
            loss= criterion(outputs, labels.long())
            
            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step(loss)
            # train loss and accuracy check:
            if counter_i % 1000 == 0 and counter_i != 0:
                print('Epoch [{}/{}], Loss: {:.4f}'.format(epoch+1, config['epochs'], loss.item()))
        val_losses = []
        mean_ious = []
        model.eval()
        for images, labels in val_loader:
            b, h, c = images.shape
            images = images.float().to(device)
            labels = labels.to(device)
            outputs = model(images)
            outputs = outputs.transpose(1, 2)
            loss = criterion(outputs, labels.long())
            val_losses.append(loss.item())
            mean_ious.append(mean_iou(model.forward_pred(images), labels.long(),num_classes=5))
        val_loss = sum(val_losses) / len(val_losses)
        miou = sum(mean_ious) / len(mean_ious)
        print(f'Epoch [{epoch+1}/{config["epochs"]}], Val Loss: {val_loss}, Mean IoU: {miou}')
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), f'./saved_model/opportunity_segmenter.pth')
        counter_i += 1
    # Test the model
    model.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.float().to(device)
            labels = labels.to(device)
            outputs = model(images)
            outputs = outputs.permute(0, 2, 1)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0) * labels.size(1)
            correct += (predicted == labels).sum().item()

        print('Test Accuracy of the model on the 10000 test images: {} %'.format(100 * correct / total))
                

if __name__ == "__main__":
    main()