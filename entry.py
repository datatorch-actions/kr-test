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
raw_categories = raw["projectById"]["labels"]
categories = []
for i, category in enumerate(raw_categories):
    categories.append({
        "id": i+1,
        "datatorch_id": category.pop("id"),
        "name": category.pop("name"),
        "metadata": category.pop("metadata"),
        "supercategory": category.pop("parentId")
    })

# Format images field
raw_images = raw["projectById"]["files"]["nodes"]
images = []
for i, image in enumerate(raw_images):
    images.append({
        "id": i+1,
        "datatorch_id": image["id"],
        "storage_id": image["linkId"],
        "path": image["path"],
        "file_name": image["name"],
        "metadata": image["metadata"],
        "date_captured": image["createdAt"]
    })

# Format annotations field
raw_annotations = raw["projectById"]["files"]["nodes"][0]["annotations"]
annotations = []

# Function to get category id index
def get_category_id_by_datatorch_label_id(categories, datatorch_id):
    for category in categories:
        if category.get("datatorch_id") == datatorch_id:
            return category.get("id")
    # Return -1 if no match is found
    return -1

for i, annotation in enumerate(raw_annotations):
    annotations.append({
        "id": i+1,
        "datatorch_id": annotation["id"],
        "datatorch_label_id": annotation["labelId"],
        "image_id": 1, # There will always only be one file
        "category_id": get_category_id_by_datatorch_label_id(categories,annotation["labelId"])
    })

# Create COCO JSON structure
coco_data = {"categories": categories, "images": images, "annotations": annotations}

set_output("returnText", coco_data)
