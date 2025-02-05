# coding=utf-8
# Copyright 2023 The Uncertainty Baselines Authors.
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

"""Tests for Wide ResNet with PI access and approximate full marginalization head."""

import tensorflow as tf
import uncertainty_baselines as ub


class WideResnetPIFullMarginalizationTest(tf.test.TestCase):

  def testWideResnetPIFullMarginalization(self):
    tf.random.set_seed(83922)
    dataset_size = 10
    batch_size = 5
    input_shape = (32, 32, 1)
    num_classes = 2
    num_annotators = 3
    pi_feature_length = 4
    num_mc_samples = 10

    features = tf.random.normal((dataset_size,) + input_shape)
    pi_features = tf.random.normal(
        (dataset_size, num_annotators, pi_feature_length))
    pi_features_fm = tf.random.normal(
        (dataset_size, num_mc_samples, num_annotators, pi_feature_length))
    coeffs = tf.random.normal([tf.reduce_prod(input_shape), num_classes])
    net = tf.reshape(features, [dataset_size, -1])
    logits = tf.matmul(net, coeffs)
    labels = tf.random.categorical(logits, 1)
    dataset = tf.data.Dataset.from_tensor_slices(
        ((features, pi_features, pi_features_fm), labels))
    dataset = dataset.repeat().shuffle(dataset_size).batch(batch_size)

    def _get_avg_annotator_loss(from_logits):

      def avg_annotator_loss(labels, output):
        """Computes average loss over examples and annotators."""

        # Flatten annotator axis.
        output = tf.reshape(output, [-1, num_classes])

        # Tile labels to match number of annotators.
        labels = tf.reshape(tf.tile(labels, [1, num_annotators]), [-1, 1])

        # Sum loss for pi and no_pi heads.
        return tf.reduce_mean(
            tf.keras.losses.sparse_categorical_crossentropy(
                labels, output, from_logits=from_logits))

      return avg_annotator_loss

    model = ub.models.wide_resnet_pi_full_marginalization(
        input_shape=input_shape,
        pi_input_shape=(num_annotators, pi_feature_length),
        depth=10,
        width_multiplier=1,
        num_classes=num_classes,
        num_mc_samples=num_mc_samples,
        l2=0.,
        version=2)
    model.compile(
        'adam',
        loss=(_get_avg_annotator_loss(True), _get_avg_annotator_loss(False)))
    history = model.fit(
        dataset, steps_per_epoch=dataset_size // batch_size, epochs=2)

    loss_history = history.history['loss']
    self.assertAllGreaterEqual(loss_history, 0.)


if __name__ == '__main__':
  tf.test.main()
