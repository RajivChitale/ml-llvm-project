import pandas as pd
import numpy as np
import json
from distributeEnv import DistributeLoopEnv
from dqn_agent import Agent
import glob
import json
import torch
from collections import deque
import os
import utils
from utils import get_parse_args

os.environ['CUDA_LAUNCH_BLOCKING'] = "1"

def run(agent, config):
    
    action_mask_flag=config.action_mask_flag
    enable_lexographical_constraint = config.enable_lexographical_constraint
    
    n_episodes=60
    # max_t=1000
    eps_start=1.0
    eps_end=0.01
    eps_decay=0.000015
    score_per_episode = []
    scores = []                        # list containing scores from each episode
    scores_window = deque(maxlen=100)  # last 100 scores
    eps = eps_start

    trained_model = config.trained_model
#    if trained_model is None:
#        trained_model = os.path.join(PWD, '../trained_model')
    
    if not os.path.exists(trained_model):
            os.makedirs(trained_model)
    
    dataset=config.dataset

    #Load the envroinment
    env = DistributeLoopEnv(config)    
    count=0 
    score = 0
    training_graphs=glob.glob(os.path.join(dataset, 'graphs/train/*.json'))
    for path in training_graphs: # Number of the iterations
        score_tensor = 0 

        # if env.O3_runtimes[utils.getllfileNameFromJSON(path)] == utils.error_runtime:
        #     print('!!!!!! Graph has runtime error ', path)
        #     continue
        with open(path) as f:
            graph = json.load(f)
        print('DLOOP New graph to the env. {} '.format(path))
        count=count+1
        # if count < 1:
        #     continue
        # print('== ',count)
        for episode in range(n_episodes):

            state, topology, focusNode = env.reset_env(graph, path)
            # agent.writer.add_graph(env.ggnn)
            while(True):
                possibleNodes_emb, possibleNodes = state

                # pass the state and  topology to get the action
                # action is
                # TODO Some change is done Here
                nextNodeIndex, merge_distribute = agent.act(state, topology, focusNode, eps)
                print("action choosed : relative={} graphNode={} MDD={}".format(nextNodeIndex, possibleNodes[nextNodeIndex],merge_distribute))
                
                # Get the next the next state from the action
                # reward is 0 till we reach the end node
                # reward will be -negative, maximize  the reward
                action=(possibleNodes[nextNodeIndex], merge_distribute) 
                next_state, reward, done, distribute, focusNode = env.step(action)
                next_possibleNodes_emb, next_possibleNodes = next_state
                # next_action_mask = topology.findAllVertaxWithZeroWeights()

                print('possibleNodes_emb : ', type(possibleNodes_emb)  , possibleNodes_emb.shape)
                print('nextNodeIndex : ', type(nextNodeIndex), nextNodeIndex)
                print('merge_distribute : ', type(merge_distribute), merge_distribute)
               
                # print('type of possibleNodes_emb : ', type(possibleNodes_emb))
                # print('type of nextNodeIndex : ', type(nextNodeIndex))
                # print('type of merge_distribute : ', type(merge_distribute))
                # put the state transitionin memory buffer
                
                # changes of AMF latter toe addedd
                agent.step((possibleNodes_emb, focusNode), (nextNodeIndex, merge_distribute), reward, next_possibleNodes_emb, done)
                

                # print('state : {}'.format(state))
                print('stored in memoey action tuple: {}'.format((nextNodeIndex, merge_distribute)))
                print('reward : {}'.format(reward))
                # print('next_state : {}'.format(next_state))
                print('done : {}'.format(done))
                print('Distribution till now : {}'.format(distribute))
                
                state = (next_possibleNodes_emb, next_possibleNodes)
#                if reward > -10:
                score += reward
                score_tensor +=reward
                if done:
                    break
                print('DLOOP Goto to Next.................')
            agent.writer.add_scalar('train/rewardStep', score_tensor , (count-1)*n_episodes + episode+1)
            agent.writer.add_scalar('train/rewardWall', score_tensor)
            scores_window.append(score)       # save most recent score
            scores.append(score)              # save most recent score
            eps = max(eps_end, eps-eps_decay) # decrease epsilon
            print('\rEpisode {}\tAverage Score: {:.2f}'.format(episode, np.mean(scores_window)), end="")
            if episode % 50 == 0:
                print('\rEpisode {}\tAverage Score: {:.2f}'.format(episode, np.mean(scores_window)))

            print('\n------------------------------------------------------------------------------------------------')
        if count % 50 == 0:
            torch.save(agent.qnetwork_local.state_dict(), os.path.join(trained_model, 'checkpoint-graphs-{count}.pth'.format(count=count)))
        agent.writer.add_scalar('train/score_per_graph', score_tensor , count)

    torch.save(agent.qnetwork_local.state_dict(), os.path.join(trained_model, 'final-model.pth'))
    utils.plot(range(1, len(scores)+1), scores, 'Total Rewards per time instant',location=config.distributed_data)
    utils.plot(range(1, len(scores_window)+1), scores_window, 'Last 100 rewards',location=config.distributed_data)
    
if __name__ == '__main__':



    config = get_parse_args()
    
    # print(config.state_size)
    print(config)
    # episodes = 100
    dqn_agent = Agent(config=config, seed=0)

    # print('config : enable_lexographical_constraint : ', config.enable_lexographical_constraint)
    run(dqn_agent, config)
    # dqn_agent.writer.add_graph(dqn_agent.qnetwork_local)

    dqn_agent.writer.flush()
    dqn_agent.writer.close()
    print('Training process finished..') 
