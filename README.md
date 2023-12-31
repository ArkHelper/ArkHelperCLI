# ArkHelperCLI
<!--A [MAA Core](github.com/MaaAssistantArknights/MaaAssistantArknights)shell，方便地批量运行MAA任务。-->

## deploy/dev
1. ``` git clone https://github.com/ArkHelper/ArkHelperCLI ```  
1. ``` cd ArkHelperCLI ``` 
1. Create folder ``` ArkHelperCLI/RuntimeComponents/MAA ``` 
1. Copy **MaaCore.dll** file and **resource** folder to ```ArkHelperCLI/RuntimeComponents/MAA```(Just confirm these objects are in the folder. Therefore, you can compile MAA's **MAACore** and **SyncRes** projects source and copy the output to this folder, or you can directly extract MAA's release package here. )
1. Create folder ``` ArkHelperCLI/Config ``` 
1. Make Config (details below)
1. Install requirements via pip
1. ``` python main.py ```

## config
ArkHelperCLI config is divided into three parts: [default_personal.yaml](/Docs/examples/default_personal.yaml), [global.yaml](/Docs/examples/global.yaml), [personal.yaml](/Docs/examples/personal.yaml).  
`default_personal.yaml` is a templete. Each task configuration configured in `personal.yaml` will be automatically generated from the template.  
Check the examples by clicking the link.