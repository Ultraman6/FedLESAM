from utils import *
from .client import Client
from time import time

class feddyn(Client):
    def __init__(self, device, model_func, received_vecs, dataset, lr, args):   
        super(feddyn, self).__init__(device, model_func, received_vecs, dataset, lr, args)
        
        # rebuild
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=lr, weight_decay=self.args.weight_decay+self.args.lamb)
    
    def train(self):
        # local training
        self.model.train()
        t_start=time()
        for k in range(self.args.local_epochs):
            for i, (inputs, labels) in enumerate(self.dataset):
                inputs = inputs.to(self.device)
                labels = labels.to(self.device).reshape(-1).long()
                
                predictions = self.model(inputs)
                loss_pred = self.loss(predictions, labels)
                
                param_list = param_to_vector(self.model)
                delta_list = self.received_vecs['Local_dual_correction'].to(self.device)
                loss_correct = torch.sum(param_list * delta_list)
                
                loss = loss_pred + self.args.lamb * loss_correct
                
                self.optimizer.zero_grad()
                loss.backward()
                
                # Clip gradients to prevent exploding
                torch.nn.utils.clip_grad_norm_(parameters=self.model.parameters(), max_norm=self.max_norm) 
                self.optimizer.step()
        t_end=time()
        print(t_end-t_start)
        last_state_params_list = get_mdl_params(self.model)
        self.comm_vecs['local_update_list'] = last_state_params_list - self.received_vecs['Params_list']
        self.comm_vecs['local_model_param_list'] = last_state_params_list

        return self.comm_vecs