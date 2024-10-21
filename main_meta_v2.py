import argparse
import time
import typing

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import torch
from torch import nn
import torch.nn.functional as F
import torch.optim as optim

import higher

from datasets.DenseLabelTaskSampler import DenseLabelTaskSampler
from datasets.PhysiQ import PhysiQ
from    torch.utils.data import DataLoader

from loss_fn import dice_coefficient_time_series
def train(db, net, device, meta_opt, epoch, log, n_train_iter):
    net.train()
    # n_train_iter = db.x_train.shape[0] // db.batchsz

    for batch_idx in range(n_train_iter):
        start_time = time.time()
        # Sample a batch of support and query images and labels.
        x_spt, y_spt, x_qry, y_qry, _ = next(db)

        task_num, setsz, h, w = x_spt.size()
        querysz = x_qry.size(1)

        # TODO: Maybe pull this out into a separate module so it
        # doesn't have to be duplicated between `train` and `test`?

        # Initialize the inner optimizer to adapt the parameters to
        # the support set.
        n_inner_iter = 5
        inner_opt = torch.optim.SGD(net.parameters(), lr=1e-1)

        qry_losses = []
        qry_accs = []
        meta_opt.zero_grad()
        for i in range(task_num):
            with higher.innerloop_ctx(
                net, inner_opt, copy_initial_weights=False
            ) as (fnet, diffopt):
                # Optimize the likelihood of the support set by taking
                # gradient steps w.r.t. the model's parameters.
                # This adapts the model's meta-parameters to the task.
                # higher is able to automatically keep copies of
                # your network's parameters as they are being updated.
                for _ in range(n_inner_iter):
                    spt_logits = fnet(x_spt[i])
                    spt_loss = F.binary_cross_entropy_with_logits(spt_logits, y_spt[i].float())
                    diffopt.step(spt_loss)

                # The final set of adapted parameters will induce some
                # final loss and accuracy on the query dataset.
                # These will be used to update the model's meta-parameters.
                qry_logits = fnet(x_qry[i])
                qry_loss = F.binary_cross_entropy_with_logits(qry_logits, y_qry[i].float())
                qry_losses.append(qry_loss.detach())
                Dice_score = dice_coefficient_time_series(qry_logits, y_qry[i].float())
                print(torch.where(qry_logits[i] > 0.5, 1, 0))
                
                qry_accs.append(Dice_score)
                # Update the model's meta-parameters to optimize the query
                # losses across all of the tasks sampled in this batch.
                # This unrolls through the gradient steps.
                qry_loss.backward()

        meta_opt.step()
        qry_losses = sum(qry_losses) / task_num
        qry_accs = 100. * sum(qry_accs) / task_num
        i = epoch + float(batch_idx) / n_train_iter
        iter_time = time.time() - start_time
        if batch_idx % 4 == 0:
            print(
                f'[Epoch {i:.2f}] Train Loss: {qry_losses:.2f} | Acc: {qry_accs:.2f} | Time: {iter_time:.2f}'
            )

        log.append({
            'epoch': i,
            'loss': qry_losses,
            'acc': qry_accs,
            'mode': 'train',
            'time': time.time(),
        })


if __name__== "__main__":
    train_dataset = PhysiQ(root="data", N_way=2, split="train", window_size=200, bg_fg=None)
    test_dataset = PhysiQ(root="data", N_way=2, split="test", window_size=200, bg_fg=None)
    train_sampler = DenseLabelTaskSampler(
            train_dataset, n_way=2, n_shot=1, batch_size=16, n_query=1, n_tasks=train_dataset.NUM_TASKS, threshold_ratio=.25
        )
    test_sampler = DenseLabelTaskSampler(
            test_dataset, n_way=2, n_shot=1, batch_size=16, n_query=1, n_tasks=test_dataset.NUM_TASKS, threshold_ratio=.25
        )

    train_loader = DataLoader(
            train_dataset,
            batch_sampler=train_sampler,
            num_workers=0,
            pin_memory=True,
            collate_fn=train_sampler.episodic_collate_fn,
        )
    
    data = next(iter(train_loader))
    x_spt, y_spt, x_qry, y_qry, true_id = data
    print(x_spt.shape)
    net = nn.Sequential(
        nn.Conv1d(in_channels=6, out_channels=64, kernel_size=3, padding=1),  # 1D conv with padding
        nn.ReLU(),
        nn.Conv1d(64, 64, 3, padding=1),
        nn.ReLU(),
        nn.MaxPool1d(2, return_indices=False),  # 1D max pooling
        nn.Conv1d(64, 64, 3, padding=1),
        nn.ReLU(),
        nn.Conv1d(64, 64, 3, padding=1),
        nn.ReLU(),
        nn.Upsample(scale_factor=2, mode='linear', align_corners=True),  # Upsampling
        nn.Conv1d(64, 64, 3, padding=1),
        nn.ReLU(),
        nn.Conv1d(64, 1, 1),  # Output layer with 1 channel
        nn.Sigmoid()  # Sigmoid activation for binary segmentation
    )

    # Ensure the output shape matches (N, 200)
    class SegmentationModel(nn.Module):
        def __init__(self):
            super(SegmentationModel, self).__init__()
            self.net = net

        def forward(self, x):
            x = x.float()
            x= x.permute(0, 2, 1)
            x = self.net(x)
            return x.squeeze(1)  # Remove the channel dimension to get (N, 200)

    model = SegmentationModel()
    
    meta_opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    for epoch in range(100):
        train(iter(train_loader), model, 'cuda', meta_opt, epoch, [], n_train_iter=1)