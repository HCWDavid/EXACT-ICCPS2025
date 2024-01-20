import torch
from config import Config
from dataset import default_splitter
from models import TransformerModel
from utilities import get_device
class DiceLoss(torch.nn.Module):
    def __init__(self):
        super(DiceLoss, self).__init__()

    def forward(self, predicted, ground_truth):
        # Flatten the tensors
        # For predicted, we need to select the probabilities for the '1' class (last channel)
        predicted_flat = predicted[:, :, 1].contiguous().view(-1)
        ground_truth_flat = ground_truth.contiguous().view(-1)

        # Compute intersection and union
        intersection = (predicted_flat * ground_truth_flat).sum()
        union = predicted_flat.sum() + ground_truth_flat.sum()

        # Compute Dice coefficient
        dice_coefficient = (2. * intersection + 1e-6) / (union + 1e-6)

        # Compute Dice loss
        dice_loss = 1 - dice_coefficient

        return dice_loss

class Manager:
    def __init__(self, config):
        self.config = config  # yaml file of config
        self.device = get_device()
        #  ntoken=6, ninp=512, nhead=8, nhid=2048, nlayers=6, dropout=0.5
        self.model = TransformerModel(ntoken=6, 
                                      ninp=config['model']['dim_inp'],
                                      nhead=config['model']['num_heads'],
                                      nhid=config['model']['dim_model'],
                                      nlayers=config['model']['num_layers'],
                                      dropout=config['model']['dropout']).to(self.device)
                                      
        # Assume config contains other necessary components like optimizer, scheduler, etc.

    def __str__(self):
        pass

    def __del__(self):
        pass
    
    

    def train(self, train_dataset):
        self.model.train()
        train_loss = 0
        optimizer = self._get_optimizer()
        criterion = self._get_criterion()
        batch_size = self.config['train']['batch_size']
        epochs = self.config['train']['epochs']

        for epoch in range(epochs):
            for i in range(0, len(train_dataset), batch_size):
                data, label = train_dataset[i:i + batch_size]
                data = data.to(self.device)
                label = label.to(self.device)
                optimizer.zero_grad()
                output = self.model(data, has_mask=False).squeeze(-1)
                loss = criterion(output, label)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
                optimizer.step()
                train_loss += loss.item()
                if i % 100 == 0 and i > 0:
                    cur_loss = train_loss / 100
                    print(f'Epoch {epoch}, iter {i}, loss {cur_loss}')
                    train_loss = 0
                if i % 1000 == 0 and i > 0:
                    # Visualization code here...
                    pass

    
    def _get_optimizer(self):
        if self.config['train']['optimizer'] == 'adam':
            return torch.optim.Adam(self.model.parameters(), lr=self.config['train']['lr'])
        elif self.config['train']['optimizer'] == 'sgd':
            return torch.optim.SGD(self.model.parameters(), lr=self.config['train']['lr'])
        else:
            raise NotImplementedError
        
    def _get_criterion(self):
        if self.config['train']['criterion'] == 'mse':
            return torch.nn.MSELoss()
        elif self.config['train']['criterion'] == 'cross_entropy':
            return torch.nn.CrossEntropyLoss()
        elif self.config['train']['criterion'] == 'dice':
            return DiceLoss()
        else:
            raise NotImplementedError



if __name__ == "__main__":
    config = Config("config.yaml")
    m = Manager(config)

    folder_name = './datasets/spar'
    train_dataset, test_dataset = default_splitter(folder_name, split=False)
    m.train(train_dataset)