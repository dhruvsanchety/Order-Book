'''
The order book contains a Dictionary for both bids and asks, where the keys are the price. The values are dictionaries 
that contain the head and tail of a linked list with orders at that price. The head of the linked list stores the correct netsize at that 
price level. There is another dictionary, where they key is the order_id, and the value is the node. Furthermore, there is a heap for both 
distinct bid and ask prices. Since the Python library heapq class defaults to a Min-Heap, the negation of the bid price is stored in the heap 
to guarantee 0(1) access to the maximum bid price. 
'''
#libraries
import pandas as pd
import csv
from heapq import heapify, heappush, heappop 

#class definition
class Node:
    def __init__(self, side, order_id, price, size, netsize):
        
        self.previous = None
        self.next = None
        self.side = side
        self.order_id = order_id
        self.price = price
        self.size = size
        self.netsize = netsize

#If side==buy, return -1*price.
def convert(price,side):
    
    if side == "buy":
        return -1*price
    else:
        return price
         
# Return other side 
def other(side): 
    
    if side == "buy":
       return "sell"
    else:
       return "buy"

#If trade can occur, return true. Otherwise, return false. 
def can_trade(side, current, heap,price_dictionary):
    
    if current.size>0 and not heap[side]==[] and ( (side == "buy" and current.price<=-heap[side][0]) or (side == "sell" and current.price>=heap[side][0]) ):
        return True
    else:
        return False

#Insert order into order book
def insert(current,side,heap,id_dictionary,price_dictionary):
    
    if not current.size == 0:
        
        dictionary = {}
        
        if current.price in price_dictionary[side]:
            
            previous = price_dictionary[side][current.price]['tail']
            previous.next=current
            current.previous=previous
            current.next=None
            dictionary['head']=price_dictionary[side][current.price]['head']
            dictionary['head'].netsize+=current.size
            dictionary['tail']=current
            
        else:
            
            price = convert(current.price,side)
            heappush(heap[side],int(price))
            dictionary['head'] = current
            dictionary['tail'] = current 
            
        id_dictionary[current.order_id]=current
        price_dictionary[side][current.price]=dictionary
    
#Delete order from order book    
def delete(node,side,heap,id_dictionary,price_dictionary):
    
    id_dictionary.pop(node.order_id)
    
    if node.previous==None:
    
        if node.next == None:
    
            price_dictionary[side].pop(node.price)
    
            if node.price == convert(heap[side][0],side):
    
                heappop(heap[side])
        else:
    
            price_dictionary[side][node.price]['head']=node.next
            node.next.previous=None
            node.next.netsize=node.netsize-node.size
    
    else:
    
        if node.next == None:
    
            node.previous.next=None
            price_dictionary[side][node.price]['tail']=node.previous
    
        else:
    
            node.previous.next=node.next
            node.next.previous = node.previous
    
        price_dictionary[side][node.price]['head'].netsize-=node.size
        
#Execute trades  
def trades(current,side,heap,id_dictionary,price_dictionary,trades_lines):
    
    while can_trade(side,current,heap,price_dictionary):
    
        line = ""
        price = convert(heap[side][0],side)
        head = price_dictionary[side][price]['head']
        size = head.size
        order_id = {}
        order_id[side]=head.order_id
        order_id[other(side)]=current.order_id
        line=str(int(price))+","
    
        if current.size>=size:
    
            line+=str(int(size))+","+str(int(order_id['buy']))+","+str(int(order_id['sell']))
            current.size-=size
            current.netsize-=size
            delete(head,side,heap,id_dictionary,price_dictionary)
    
        else:
    
            line+=str(int(current.size))+","+str(int(order_id['buy']))+","+str(int(order_id['sell']))
            head.size-=current.size
            head.netsize-=current.size
            current.size=0
            current.netsize=0
    
        trades_lines.append(line)    
        
#Main     
def run(inputPath):
    
    #paths
    array = inputPath.split('/')
    path = ""
    for i in range(len(array)-1):
        path+=array[i]
        path+="/"
    bbos_path=path+"bbos.csv"
    trades_path=path+"trades.csv"
    
    #lines 
    bbos_lines=['bid_price,bid_size,ask_price,ask_size']
    trades_lines=['trade_price,trade_size,buy_order_id,sell_order_id']
    
    #variables
    price_dictionary = {'buy': {},'sell': {}}
    id_dictionary = {}
    orders = pd.read_csv(inputPath)
    
    #heaps
    heap = {'buy': [],'sell': []}
    heapify(heap['buy']) 
    heapify(heap['sell'])
    
    for index, row  in orders.iterrows():
    
        action=row['action']
        order_id=row['order_id']
           
        if action=="insert":
            
            side=row['side']
            price = row['price']
            size = row['size']
            current = Node(side,order_id,price,size,size)
            
            #Excute
            trades(current,other(side),heap,id_dictionary,price_dictionary,trades_lines)
            #Add to order book if size>0
            insert(current,side,heap,id_dictionary,price_dictionary)
        
        #If action == "cancel"
        else:  
            if order_id in id_dictionary:
                node=id_dictionary[order_id]
                side=node.side
                delete(node,side,heap,id_dictionary,price_dictionary)
               
        #bbos
        best_bid = Node('buy',0,0,0,0)
        if not heap['buy'] == []:
            best_bid = price_dictionary['buy'][-1*heap['buy'][0]]['head']
        
        best_ask = Node('sell',0,0,0,0)
        if not heap['sell'] == []:
            best_ask = price_dictionary['sell'][heap['sell'][0]]['head']
        
        line = str(int(best_bid.price)) + "," + str(int(best_bid.netsize)) + "," + str(int(best_ask.price)) + "," + str(int(best_ask.netsize))
        bbos_lines.append(line)
           
    #write
    with open(bbos_path, 'w') as csvfile:
        csvfile.writelines("%s\n" % line for line in bbos_lines)
   
    with open(trades_path, 'w') as csvfile:
        csvfile.writelines("%s\n" % line for line in trades_lines)

    return bbos_path, trades_path