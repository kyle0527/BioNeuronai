import numpy as np

from bioneuronai.curiosity import CuriosityDrivenNet


def test_intrinsic_reward_monotonicity():
    net = CuriosityDrivenNet(input_dim=2, hidden_dim=4, intrinsic_gain=1.0)

    familiar_input = [0.25, 0.25]
    for _ in range(5):
        net.forward(familiar_input)

    _, familiar_novelties = net.forward(familiar_input)
    familiar_reward = net.intrinsic_reward(familiar_novelties)

    novel_input = [0.9, 0.1]
    _, novel_novelties = net.forward(novel_input)
    novel_reward = net.intrinsic_reward(novel_novelties)

    for _ in range(5):
        net.forward(novel_input)
    _, repeated_novelties = net.forward(novel_input)
    repeated_reward = net.intrinsic_reward(repeated_novelties)

    assert novel_reward > familiar_reward
    assert repeated_reward < novel_reward
    assert familiar_reward >= 0.0
    assert repeated_reward >= 0.0


def test_intrinsic_reward_uses_last_forward():
    net = CuriosityDrivenNet(input_dim=2, hidden_dim=3)
    _, novelties = net.forward([0.1, 0.9])
    reward_with_argument = net.intrinsic_reward(novelties)
    reward_without_argument = net.intrinsic_reward()

    assert np.isclose(reward_with_argument, reward_without_argument)
