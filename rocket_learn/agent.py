from abc import abstractmethod, ABC
from typing import List, Optional

import numpy as np
import torch as th
from torch.distributions import Categorical


class BaseAgent(ABC):
    def __init__(self, index_action_map: Optional[np.ndarray] = None):
        if index_action_map is None:
            self.index_action_map = np.eye(4)  # np.array([
            #     [0., 1.],
            # ])
        else:
            self.index_action_map = index_action_map

    def forward_actor_critic(self, obs):
        raise NotImplementedError

    def forward_actor(self, obs):
        return self.forward_actor_critic(obs)[0]

    def forward_critic(self, obs):
        return self.forward_actor_critic(obs)[1]

    def get_action_distribution(self, obs) -> List[Categorical]:
        if isinstance(obs, np.ndarray):
            obs = th.from_numpy(obs).float()
        logits = self.forward_actor(obs)

        return [Categorical(logits=logit) for logit in logits]

    def get_action_indices(self, distribution: List[Categorical], deterministic=False, include_log_prob=False,
                           include_entropy=False):
        if deterministic:
            action_indices = th.stack([th.argmax(dist.logits) for dist in distribution])
        else:
            action_indices = th.stack([dist.sample() for dist in distribution])

        returns = [action_indices.numpy()]
        if include_log_prob:
            # SOREN NOTE:
            # adding dim=1 is causing it to crash

            log_prob = th.stack(
                [dist.log_prob(action) for dist, action in zip(distribution, th.unbind(action_indices, dim=-1))], dim=-1
            ).sum(dim=-1)
            returns.append(log_prob)
        if include_entropy:
            entropy = th.stack([dist.entropy() for dist in distribution], dim=1).sum(dim=1)
            returns.append(entropy)
        return tuple(returns)

    def get_action(self, action_indices) -> np.ndarray:
        return self.index_action_map[np.arange(len(self.index_action_map)), action_indices]

    @abstractmethod
    def get_model_params(self, params):
        raise NotImplementedError

    @abstractmethod
    def set_model_params(self, params) -> None:
        raise NotImplementedError
