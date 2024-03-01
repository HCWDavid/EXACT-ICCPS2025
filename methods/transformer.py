import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torch
from torch.nn.modules.transformer import TransformerEncoder, TransformerEncoderLayer
import torch.nn.functional as F

# from utilities import printc
class TransformerModel(nn.Module):
    """Container module with an encoder, a recurrent or transformer module, and a decoder."""

    def __init__(self, num_classes=5, in_channels=6, ninp=64, num_heads=1, embed_dims=256, num_layers=6, dropout=0.1, init_std=.02, activation='relu'):
        super(TransformerModel, self).__init__()
        self.input_emb = nn.Linear(in_channels, ninp)
        self.ninp = ninp
        self.relu = nn.ReLU()
        # modulelist:
        encoder_layer = nn.TransformerEncoderLayer(d_model=ninp, nhead=num_heads, dim_feedforward=embed_dims, dropout=dropout, activation=activation, batch_first=True)
        encoder_norm = nn.LayerNorm(ninp)   
        self.transformer_encoder = TransformerEncoder(encoder_layer, num_layers, norm=encoder_norm)
        self.decoder = nn.Linear(ninp, num_classes)
        self.init_std = init_std
        # max layer:
        # self.max = nn.MaxPool1d(100)
        
    def init_weights(self):
        nn.init.trunc_normal_(self.input_emb.weight, std=self.init_std)
        nn.init.trunc_normal_(self.decoder.weight, std=self.init_std)
        # xaiver initialization for Transformer:
        for param in self.transformer_encoder.parameters():
            if param.dim() > 1:
                nn.init.xavier_uniform_(param)
        
                    
    def forward(self, src):
        src = self.input_emb(src)
        src = self.relu(src)
        output = self.transformer_encoder(src)
        output = self.decoder(output)
        return output
    
    def forward_pred(self, inputs):
        masks = self.forward(inputs)
        masks = masks.permute(0, 2, 1)
        probabilities = F.softmax(masks, dim=1)
        pred = torch.argmax(probabilities, dim=1)
        return pred

if __name__ == '__main__':
    # print how many parameters are in the model
    transformer = TransformerModel(in_channels=6, embed_dims=256)
    print('Number of trainable parameters:', sum(p.numel() for p in transformer.parameters() if p.requires_grad))
    inp = torch.rand(32, 300, 6)
    out = transformer(inp)