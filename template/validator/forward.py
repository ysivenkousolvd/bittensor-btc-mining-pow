# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2024 Yahor Sivenkou

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import bittensor as bt

from template.protocol import Dummy, BitcoinSynapse
from template.validator.reward import get_rewards
from template.utils.uids import get_random_uids


async def forward(self):
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self (:obj:`bittensor.neuron.Neuron`): The neuron object which contains all the necessary state for the validator.

    """
    miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)

    # The dendrite client queries the network.
    request_data = f"Block data {self.btc_block}"
    bt.logging.debug(
        f"Validator request: "
        f"block: {self.btc_block}, "
        f"nonce: {self.nonce}, "
        f"data: {request_data}, "
        f"previous_hash: {self.previous_hash}"
    )

    responses = await self.dendrite(
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        synapse=BitcoinSynapse(nonce=self.nonce, data=request_data, previous_hash=self.previous_hash),
        deserialize=True,
    )
    # Log the results for monitoring purposes.
    bt.logging.info(f"Received responses: {responses}")

    rewards = get_rewards(self, query=self.step, responses=responses, difficulty=self.difficulty)

    bt.logging.info(f"Scored responses: {rewards}")
    self.update_scores(rewards, miner_uids)
    if rewards.any():
        bt.logging.info(f"Block {self.btc_block} has been mined")
        self.nonce = 0
        self.previous_hash = [(response, reward) for response, reward in zip(responses, rewards) if reward][0][0]
        self.btc_block += 1
    else:
        self.nonce += 1
