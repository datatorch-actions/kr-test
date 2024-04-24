import os, json

from datatorch import get_input, agent, set_output, ApiClient

api = ApiClient()
directory = os.path.dirname(os.path.abspath(__file__))
agent_dir = agent.directories().root

dt_fileId = get_input("fileId")
command = get_input("command")
projectId = get_input("projectId")

# Query to get file and annotation data to be converted to COCO
GetNewestExport = """
query GetFileData($projectId:ID!, $fileId:String!="0e8ea8d1-6abc-4781-b7be-cee1c65b2949",){
  projectById(id:$projectId) {
    files(input: 
      { 
      	where: {
    			id: {
          	equals:$fileId
        	}
    		},
      	perPage:1,
      	page: 1
    	}
  	) {
      nodes{
        id
        annotations {
          id
          metadata
          labelId
          sourcesJson
        }
      }
    }
    labels {
      id
      name
      metadata
      parentId
    }
  }
}
"""

raw = api.execute(GetNewestExport, params={"projectId": projectId, "fileId": dt_fileId})
categories = raw["projectById"]["labels"]

# Create COCO JSON structure
coco_data = {
    "categories": categories
}

set_output("returnText", categories)
