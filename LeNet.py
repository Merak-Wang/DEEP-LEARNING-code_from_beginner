import torch
from torch import nn
from d2l import torch as d2l


class Reshape(torch.nn.Module):
    def forward(self,x):
        return x.view(-1,1,28,28)

#构建网络
# net = nn.Sequential(Reshape(),nn.Conv2d(1,6,kernel_size=5,padding=2),nn.Sigmoid(),
#                     nn.AvgPool2d(kernel_size=2,stride=2),
#                     nn.Conv2d(6,16,kernel_size=5),nn.Sigmoid(),
#                     nn.AvgPool2d(kernel_size=2,stride=2),nn.Flatten(),
#                     #全连接层，有两个隐藏层的MLP
#                     nn.Linear(16*5*5,120),nn.Sigmoid(),
#                     nn.Linear(120,84),nn.Sigmoid(),
#                     nn.Linear(84,10))

#试试调参
net = nn.Sequential(Reshape(),nn.Conv2d(1,6,kernel_size=5,padding=2),nn.ReLU(),
                    nn.AvgPool2d(kernel_size=2,stride=2),
                    nn.Conv2d(6,16,kernel_size=5),nn.ReLU(),
                    nn.AvgPool2d(kernel_size=2,stride=2),nn.Flatten(),
                    #全连接层，有两个隐藏层的MLP
                    nn.Linear(16*5*5,120),nn.ReLU(),
                    nn.Linear(120,84),nn.ReLU(),
                    nn.Linear(84,10))


# X = torch.rand(size=(1, 1, 28, 28), dtype=torch.float32)
# for layer in net:
#     X = layer(X)
#     print(layer.__class__.__name__,'output shape: \t',X.shape)


batch_size = 256
train_iter , test_iter = d2l.load_data_fashion_mnist(batch_size=batch_size)


def evaluate_accuracy_gpu(net,data_iter,device=None):
    if isinstance(net,torch.nn.Module):
        net.eval()
        if not device:
            device = next(iter(net.parameters())).device
    metric = d2l.Accumulator(2)
    for X,y in data_iter:
        if isinstance(X,list):
            X = [x.to(device) for x in X]
        else:
            X = X.to(device)
        y = y.to(device)
        metric.add(d2l.accuracy(net(X),y),y.numel())
    return metric[0] / metric[1]


def train_ch6(net,train_iter,test_iter,num_epochs,lr,device):
    #初始化
    def init_weights(m):
        if type(m) == nn.Linear or type(m) == nn.Conv2d:
            nn.init.xavier_uniform_(m.weight)
    net.apply(init_weights)
    print('training on',device)
    #将网络移动到GPU
    net.to(device)
    #定义优化器和损失函数
    optimizer = torch.optim.SGD(net.parameters(),lr=lr)
    loss = nn.CrossEntropyLoss()
    #动画
    animator = d2l.Animator(xlabel='epoch', xlim=[1, num_epochs],
                            legend=['train loss', 'train acc', 'test acc'])
    timer , num_batches = d2l.Timer() , len(train_iter)
    #开始训练
    for epoch in range(num_epochs):
        metric = d2l.Accumulator(3)
        #切换到训练模式
        net.train()
        for i,(X,y) in enumerate(train_iter):
            timer.start()
            #训练过程
            optimizer.zero_grad()
            X,y = X.to(device),y.to(device)
            y_hat = net(X)
            l = loss(y_hat,y)
            l.backward()
            optimizer.step()
            #输出精度
            metric.add(l*X.shape[0],d2l.accuracy(y_hat,y),X.shape[0])
            timer.stop()
            train_l = metric[0] / metric[2]
            train_acc = metric[1] / metric[2]
            if (i + 1) % (num_batches // 5) == 0 or i == num_batches - 1:
                animator.add(epoch + (i + 1) / num_batches,(train_l, train_acc, None))
        test_acc = evaluate_accuracy_gpu(net, test_iter)
        animator.add(epoch + 1, (None, None, test_acc))
    print(f'loss {train_l:.3f}, train acc {train_acc:.3f}, 'f'test acc {test_acc:.3f}')
    print(f'{metric[2] * num_epochs / timer.sum():.1f} examples/sec 'f'on {str(device)}')

# lr , num_epochs = 0.9 , 10

lr , num_epochs = 0.1 , 30
if __name__ == '__main__':
    train_ch6(net,train_iter,test_iter,num_epochs=num_epochs,lr=lr,device=d2l.try_gpu())



