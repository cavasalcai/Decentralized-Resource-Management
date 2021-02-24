# Decentralized Resource Management for Latency-Sensitive IoT Applications with Satisfiability

A decentralized resource management technical  framework  aiming  to  deploy  applications at  the  edge  of  the  network,  guaranteeing  adherence  to (i)  defined  latency  Service  Level  Agreements  (SLAs)  and (ii)  resource  preferences  of  participating edge nodes. 


## Instalation

Download the framework and install all requirements from the *requirements.txt* file. The project was developed in Python 2.7.

## Framework details

First, the user must provide two different input JSON files:
 * application model file, where the application's requirements and communication path is described, stored in the app folder.
 * target edge architecture file, stored in the edgeArchitecture folder. Here, provide the IP addresses of the edge nodes where the API resides or use localhost if the nodes run locally on the same machine.


In our framework there are two important entities, i.e., the coordinator node and the coolaborator nodes:
* *dispatcher.py*: represents the functionality of the coordinator node.
* *edgenode_api_main.py*: represents the functionality of the collaborator nodes.

More details can be found in our technical paper.

## Usage

First, the *edgenode_api_main.py* must run on the collaborators. To do so, we can use the following command:

```bash
python edgenode_api_main.py <port_name>
```

By default, if *<port_name>* is omitted, the port will be set to 5000.

Once all collaborators are active and the two imput files are prepared, we can execute *dispatcher.py*, using the following command:

```bash
 python dispatcher.py -a "antivirusApp" -e "edgeNodes" -s
```
In the command above we tell the dispatcher that the application model file name is *antivirusApp* and the target edge architecture is described in *edgeNodes* JSON file. Finally, to see the deployment strategy on the stdout, we add the *-s* argument.

For a complete list of arguments that can be parsed as input to *dispatcher.py* please run:

```bash
 python dispatcher.py -h
```



