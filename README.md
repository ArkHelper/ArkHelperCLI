# ArkHelperCLI
<!--A [MAA Core](github.com/MaaAssistantArknights/MaaAssistantArknights)shell，方便地批量运行MAA任务。-->

## deploy/dev
1. ``` git clone https://github.com/ArkHelper/ArkHelperCLI ```  
1. ``` cd ArkHelperCLI ``` 
1. ``` mkdir RuntimeComponents ``` 
1. ``` cd RuntimeComponents ```
1. ``` mkdir MAA ``` (ArkHelperCLI/RuntimeComponents/MAA folder is the root directory of MAA. )
1. Copy **MaaCore.dll** file and **resource** folder to ```ArkHelperCLI/RuntimeComponents/MAA```(Just confirm that MaaCore.dll is in the folder. Therefore, you can compile MAA's **MAACore** and **SyncRes** projects and copy the output files to this folder, or you can directly extract MAA's release package here. )
1. ``` cd ArkHelperCLI ```
1. ``` python main.py ```