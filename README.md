# FactorioHGNN

**FactorioHGNN** is a specialized AI project designed to solve open ended logistic and optimization problems within the game *Factorio* using Hypergraph Neural Networks (HGNNs).

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

* **Windows and Mac OS:**
    * python version 3.1x or later
    * pip install numpy, pytorch, factorio-rcon-py, plotly, tqdm, timeit
    * Factorio Headless Linux Client https://www.factorio.com/download
    * Docker or Docker Desktop (WSL2 recommended for Windows)
    * Choose a location on your computer where the server's data (saves, mods, config) will be permanently stored. This location is called the HOST PATH.
        * Windows: A simple path like C:\factorio_data is recommended
        * Linux/macOS: A common path is /opt/factorio or /home/user/factorio-server
    * Use the command below, replacing the placeholder [HOST_PATH] with the actual path you chose
    * For Windows use: `docker run -d -p 34197:34197/udp -p 27015:27015/tcp -v C:/factorio_data:/factorio --name factorio --restart=unless-stopped factoriotools/factorio`
    * For Mac OS/Linux use: `docker run -d \
  -p 34197:34197/udp \
  -p 27015:27015/tcp \
  -v [HOST_PATH]:/factorio \
  --name factorio \
  --restart=unless-stopped \
  factoriotools/factorio`
`
    * Finally Clone the repository and add the rcon_bridge mod to the headless client in the folder you defined and to your factorio installation if you want to join to observe the AI via localhost:
* **Linux:** (hasnt been tested but should work the same)

* **Optional:**
    * You can download yEd to visualize the whole factory the way the AI sees it. This can be useful for determining issues and misinterpretations and to view the progress of the AI without joining the server/ opening the game.


## Usage
* main.py uses the finished jimbo_dqn_weights.pth to inference and select actions to steer the AI.
* Train_dqn.py trains the AI based on parameters set at the top and in config.py.
* Plotting.py can show you the relevant scores of the collected data during training.
* Graph_utils.py can be used to visualize the factory the AI built during training or inferencing. Also this can be used to visualize any factory as long as you put your savegame onto the server. However this needs the optional yEd to be installed, to visualize the graphml files.
## Project Structure

* [TODO: Describe key directories]

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
