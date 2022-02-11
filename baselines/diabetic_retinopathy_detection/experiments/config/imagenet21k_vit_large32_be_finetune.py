# coding=utf-8
# Copyright 2022 The Uncertainty Baselines Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=line-too-long
r"""ViT-L/32 + BatchEnsemble finetuning on RETINA.
"""
# pylint: enable=line-too-long

import ml_collections


def get_config():
  """Config."""
  config = ml_collections.ConfigDict()

  # Data load / output flags

  # The directory where the model weights and training/evaluation summaries
  #   are stored.
  config.output_dir = (
      '/tmp/diabetic_retinopathy_detection/vit-32-i21k/batchensemble')

  # Fine-tuning dataset
  config.data_dir = 'gs://ub-data/retinopathy'

  # REQUIRED: distribution shift.
  # 'aptos': loads APTOS (India) OOD validation and test datasets.
  #   Kaggle/EyePACS in-domain datasets are unchanged.
  # 'severity': uses DiabeticRetinopathySeverityShift dataset, a subdivision
  #   of the Kaggle/EyePACS dataset to hold out clinical severity labels as OOD.
  config.distribution_shift = 'aptos'

  # If provided, resume training and/or conduct evaluation using this
  #   checkpoint. Will only be used if the output_dir does not already
  #   contain a checkpointed model. See `checkpoint_utils.py`.
  config.resume_checkpoint_path = None

  config.prefetch_to_device = 2
  config.trial = 0

  # Logging and hyperparameter tuning

  config.use_wandb = False  # Use wandb for logging.
  config.wandb_dir = 'wandb'  # Directory where wandb logs go.
  config.project = 'ub-debug'  # Wandb project name.
  config.exp_name = None  # Give experiment a name.
  config.exp_group = None  # Give experiment a group name.

  # Model Flags

  # TODO(nband): fix issue with sigmoid loss.
  config.num_classes = 2

  # pre-trained model ckpt file
  # !!!  The below section should be modified per experiment
  config.model_init_and_random_sign_init = (
    'gs://ub-checkpoints/ImageNet21k_BE-L32/baselines-jft-0209_205214/1/'
    'checkpoint.npz', -0.75)

  # Model section
  config.model = ml_collections.ConfigDict()
  config.model.patches = ml_collections.ConfigDict()
  config.model.patches.size = [32, 32]
  config.model.hidden_size = 1024
  config.model.transformer = ml_collections.ConfigDict()
  config.model.transformer.attention_dropout_rate = 0.
  config.model.transformer.dropout_rate = 0.
  config.model.transformer.mlp_dim = 4096
  config.model.transformer.num_heads = 16
  config.model.transformer.num_layers = 24
  config.model.classifier = 'token'  # Or 'gap'

  # This is "no head" fine-tuning, which we use by default
  config.model.representation_size = None

  # BatchEnsemble parameters.
  config.model.transformer.be_layers = (21, 22, 23)
  config.model.transformer.ens_size = 3
  config.fast_weight_lr_multiplier = 1.0

  # Preprocessing

  # Input resolution of each retina image. (Default: 512)
  config.pp_input_res = 512  # pylint: disable=invalid-name
  pp_common = f'|onehot({config.num_classes})'
  config.pp_train = (
      f'diabetic_retinopathy_preprocess({config.pp_input_res})' + pp_common)
  config.pp_eval = (
      f'diabetic_retinopathy_preprocess({config.pp_input_res})' + pp_common)

  # Training Misc
  config.batch_size = 512  # using TPUv3-64
  config.seed = 0  # Random seed.
  config.shuffle_buffer_size = 15_000  # Per host, so small-ish is ok.

  # Optimizer section
  config.optim_name = 'Momentum'
  config.optim = ml_collections.ConfigDict()
  config.loss = 'softmax_xent'  # or 'sigmoid_xent'
  config.grad_clip_norm = 1.0
  config.weight_decay = None  # No explicit weight decay

  config.lr = ml_collections.ConfigDict()
  config.lr.base = 1e-3  # Set in sweep.
  config.lr.decay_type = 'linear'

  # The dataset is imbalanced (e.g., in Country Shift, we have 19.6%, 18.8%,
  # 19.2% positive examples in train, val, test respectively).
  # None (default) will not perform any loss reweighting.
  # 'constant' will use the train proportions to reweight the binary cross
  #   entropy loss.
  # 'minibatch' will use the proportions of each minibatch to reweight the loss.
  config.class_reweight_mode = None

  # Evaluation Misc
  config.only_eval = False  # Disables training, only evaluates the model
  config.use_validation = True  # Whether to use a validation split
  config.use_test = True  # Whether to use a test split

  # Step Counts
  config.total_and_warmup_steps = (10_000, 500)
  config.log_training_steps = 100
  config.log_eval_steps = 1000
  # NOTE: eval is very fast O(seconds) so it's fine to run it often.
  config.checkpoint_steps = 1000
  config.checkpoint_timeout = 1

  config.args = {}
  return config
