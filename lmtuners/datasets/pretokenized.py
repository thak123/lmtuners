import torch
from lmtuners.utils import mask_tokens
from torch.utils.data import ConcatDataset, Dataset


class PreTokenizedFileDataset(Dataset):
    def __init__(self, path):
        self.path = path

        data = torch.load(path)
        self.ids = data['ids']
        self.attention_masks = data['attention_masks']
        self.special_tokens_masks = data['special_tokens_masks']
        if 'token_type_ids' in data:
            self.token_type_ids = data['token_type_ids']
        else:
            self.token_type_ids = [None] * len(self.ids)

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, i):
        return self.ids[i], self.attention_masks[i], self.special_tokens_masks[i], self.token_type_ids[i]


def create_pretokenized_dataset(paths):
    datasets = [PreTokenizedFileDataset(p) for p in paths]
    dataset = ConcatDataset(datasets)
    return dataset


class PreTokenizedCollater(object):
    def __init__(self,
                 mlm=True,
                 mlm_prob=0.15,
                 pad_token_id=None,
                 mask_token_id=None,
                 vocab_size=None,
                 cls_token_id=None,
                 rand_replace=True):
        self.mlm = mlm
        self.mlm_prob = mlm_prob
        self.pad_token_id = pad_token_id
        self.mask_token_id = mask_token_id
        self.vocab_size = vocab_size
        self.cls_token_id = None
        self.rand_replace = rand_replace

    def __call__(self, examples):
        inputs, attention_masks, special_tokens_masks, token_type_ids = zip(*examples)
        inputs = torch.stack(inputs).long()
        attention_masks = torch.stack(attention_masks).long()
        special_tokens_masks = torch.stack(special_tokens_masks)

        if token_type_ids[0] is not None:
            token_type_ids = torch.stack(token_type_ids).long()
        else:
            token_type_ids = None

        if self.mlm:
            inputs, labels = mask_tokens(inputs, special_tokens_masks,
                                         self.pad_token_id, self.mask_token_id,
                                         self.vocab_size, self.mlm_prob,
                                         rand_replace=self.rand_replace)
            return inputs, labels, attention_masks, token_type_ids
        else:
            return inputs, inputs, attention_masks, token_type_ids
