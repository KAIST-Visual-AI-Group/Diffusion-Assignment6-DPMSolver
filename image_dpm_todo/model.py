from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm


class DiffusionModule(nn.Module):
    def __init__(self, network, scheduler, **kwargs):
        super().__init__()
        self.network = network
        self.scheduler = scheduler

    def get_loss(self, x0, class_label=None, noise=None):
        B = x0.shape[0]
        timestep = self.scheduler.uniform_sample_t(B, self.device)
        x_noisy, noise = self.scheduler.add_noise(x0, timestep)
        noise_pred = self.network(x_noisy, timestep=timestep, class_label=class_label)

        loss = F.mse_loss(noise_pred.flatten(), noise.flatten(), reduction="mean")
        return loss
    
    @property
    def device(self):
        return next(self.network.parameters()).device

    @property
    def image_resolution(self):
        return self.network.image_resolution

    @torch.no_grad()
    def sample(
        self,
        shape,
        num_inference_timesteps,
        order,
        return_traj=False,
        class_label: Optional[torch.Tensor] = None,
        guidance_scale: Optional[float] = 7.5,
    ):
        batch_size = shape[0]
        x_T = torch.randn(shape).to(self.device)

        self.var_scheduler.set_timesteps(num_inference_timesteps//order)
        assert guidance_scale > 1.0

        ######## TODO ########
        # Implement the classifier-free guidance.
        # DO NOT change the code outside this part.
        # You can copy & paste your implementation of previous Assignments.
        assert class_label is not None
        assert len(class_label) == batch_size, f"len(class_label) != batch_size. {len(class_label)} != {batch_size}"
        #######################

        traj = [x_T]
        for t in tqdm(self.scheduler.timesteps):
            x_t = traj[-1]
            ######## TODO ########
            # DO NOT change the code outside this part.
            # Implement the classifier-free guidance.
            # You can copy & paste your implementation of previous Assignments.
            noise_pred = x_t_prev
            x_t_prev = self.scheduler.step(x_t, t, noise_pred, class_label=class_label)
            #######################


            traj[-1] = traj[-1].cpu()
            traj.append(x_t_prev.detach())

        if return_traj:
            return traj
        else:
            return traj[-1]

    def save(self, file_path):
        hparams = {
                "network": self.network,
                "var_scheduler": self.var_scheduler,
                } 
        state_dict = self.state_dict()

        dic = {"hparams": hparams, "state_dict": state_dict}
        torch.save(dic, file_path)

    def load(self, file_path):
        dic = torch.load(file_path, map_location="cpu")
        hparams = dic["hparams"]
        state_dict = dic["state_dict"]

        self.network = hparams["network"]
        self.var_scheduler = hparams["var_scheduler"]

        self.load_state_dict(state_dict)
