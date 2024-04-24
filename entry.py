import os

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
        linkId
        path
        name
        metadata
        createdAt
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

# Format categories field
categories = raw["projectById"]["labels"]
for i, category in enumerate(categories):
    category["datatorch_id"] = category.pop("id")
    category["id"] = i + 1
    category["datatorch_id"] = category.pop("datatorch_id")
    category["name"] = category.pop("name")
    category["metadata"] = category.pop("metadata")
    category["supercategory"] = category.pop("parentId")

# Format images field
raw_images = raw["projectById"]["files"]["nodes"]
images = []
for i, image in enumerate(raw_images):
    images.append({
        "id": i+1,
        "datatorch_id": image.pop("datatorch_id"),
        "storage_id": image.pop("linkId"),
        "path": image.pop("path"),
        "file_name": image.pop("name"),
        "metadata": image.pop("metadata"),
        "date_captured": image.pop("createdAt")
    })


# Create COCO JSON structure
coco_data = {"categories": categories, "images": images}

set_output("returnText", coco_data)
