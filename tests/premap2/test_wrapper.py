import torch

from premap2.wrapper import PremapInPath, construct_config, premap

from .utils import model_conv, model_linear


def test_construct_config():
    def post(config):
        assert config["debug"]["asserts"]

    with PremapInPath():
        construct_config(False, post, {"asserts": True})
        construct_config(False, post, asserts=True)
        construct_config(False, post, {"asserts": False}, asserts=True)


def test_wrapper_fc(tmp_path, iter: int = 10):
    assert iter >= 0, "PREMAP never needed more than one domain"
    model = model_linear(20, 10, 5, 1).eval()
    x = torch.randn((1, 20))
    with torch.no_grad():
        list(model.parameters())[-1] -= model(x).ravel()
    res = premap(
        dataset=[x, 0, 1.0, 0.0],
        model=model,
        result_dir=tmp_path,
        epsilon=1.0,
        norm=2,
        num_outputs=1,
        sample_num=100,
        branch_budget=10,
    )
    result = torch.load(res[0])
    if len(result["domains"]) <= 1:
        return test_wrapper_fc(tmp_path, iter=iter - 1)


def test_wrapper_conv(tmp_path, iter: int = 10):
    assert iter >= 0, "PREMAP never needed more than one domain"
    model = model_conv(3, 4, 5, 4, 1).eval()
    x = torch.randn((1, 3, 5, 5))
    with torch.no_grad():
        list(model.parameters())[-1] *= 2.0
        list(model.parameters())[-1] -= model(x).ravel()
    res = premap(
        dataset=[x, 0, 1.0, 0.0],
        model=model,
        result_dir=tmp_path,
        patch_x=1,
        patch_y=1,
        patch_h=3,
        patch_w=3,
        atk_tp="patch",
        num_outputs=1,
        sample_num=100,
        branch_budget=10,
    )
    result = torch.load(res[0])
    if len(result["domains"]) <= 1:
        return test_wrapper_conv(tmp_path, iter=iter - 1)
