# FactorioHGNN

**FactorioHGNN** is a specialized AI project designed to solve open ended logistic and optimization problems within the game *Factorio* using Hypergraph Neural Networks (HGNNs).

CURRENTLY WE **DO NOT** RECOMMEND YOU INSTALL THIS. This is a prealpha in development version that has yet to be thoroughly tested. Also were limiting the game to red circuits without any mods or dlcs. 

Unlike generic Large Language Models (LLMs) that struggle with spatial reasoning and long term planning in complex logistical environments, FactorioHGNN leverages the natural graph structure of factories where belts, inserters, and assemblers form hyper edges in a graph to achieve superior reasoning capabilities.

## Research Paper

This project is the official implementation for the paper:

**FactorioHGNN: Superseding LLM reasoning in open ended logistic problems via Hypergraph Neural Networks**
[📄 Link to Paper (Coming Soon)](#)

## The Benchmark: Factorio Learning Environment (FLE)

This project aims to beat the scores of the **Factorio Learning Environment (FLE)**, a benchmark created by Jack Hopkins to test the limits of AI planning and spatial reasoning. While our Project does not implement the same benchmark and gym environment. The production score however will be comparable.

While Hopkins' research highlights the limitations of frontier models (like Claude 3.5 Sonnet and GPT-4o) in handling the exponential complexity of Factorio, our approach moves away from token based reasoning. Instead, we utilize a purpose built HGNN to directly model the factory's topology, aiming to decisively beat the LLM score's Jack Hopkins et al. identified.

* **FLE Repository:** [JackHopkins/factorio-learning-environment](https://github.com/JackHopkins/factorio-learning-environment)
* **FLE Paper:** [Factorio Learning Environment (arXiv)](https://arxiv.org/abs/2503.09617)

## Installation
We currently do not recommend installation. Were working on major changes and upgrades.
If you do want to get this running the main file to get running is train_dqn.py
You need docker (also we recommend Streamlit to run streamlitupdate.py) and all the python packages within the code.

## Usage


## Project Structure


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
