import os

import numpy as np

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
    categories.append(
        {
            "id": i + 1,
            "datatorch_id": category.pop("id"),
            "name": category.pop("name"),
            "metadata": category.pop("metadata"),
            "supercategory": category.pop("parentId"),
        }
    )

# Format images field
raw_images = raw["projectById"]["files"]["nodes"]
images = []
for i, image in enumerate(raw_images):
    images.append(
        {
            "id": i + 1,
            "datatorch_id": image["id"],
            "storage_id": image["linkId"],
            "path": image["path"],
            "file_name": image["name"],
            "metadata": image["metadata"],
            "date_captured": image["createdAt"],
        }
    )

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


# Function to generate segmentation and bbox fields
def generate_segmentation_and_bbox(sourcesJson):
    returnObject = {"segmentation": []}
    hasPoly = False
    hasRect = False
    sourceWithPathData = None
    sourceWithBoxData = None

    for source in sourcesJson:
        if source["type"] in ["PaperSegmentations"]:
            hasPoly = True
        if source["type"] in ["PaperBox"]:
            hasRect = True

    isShape = hasPoly or hasRect

    if not isShape:
        return returnObject

    for source in sourcesJson:
        if "pathData" in source:
            sourceWithPathData = source
            # This wont work for multi polygon annotations for now

        if sourceWithPathData is not None:
            # It has a polygon which takes precidence in segmentaion field
            returnObject["segmentation"].extend(
                [np.array(polygon).flatten() for polygon in source["pathData"]]
            )
        else:
            if (
                "x" in source
                and "y" in source
                and "width" in source
                and "height" in source
            ):
                sourceWithBoxData = source
                # It is a box only
                returnObject["segmentation"] = [
                    source["x"],
                    source["y"],
                    source["x"] + source["width"],
                    source["y"],
                    source["x"] + source["width"],
                    source["y"] + source["height"],
                    source["x"],
                    source["y"] + source["height"],
                ]

    if sourceWithBoxData is not None:
        returnObject["bbox"] = [
            sourceWithBoxData["x"],
            sourceWithBoxData["y"],
            sourceWithBoxData["width"],
            sourceWithBoxData["height"],
        ]

    return returnObject


for i, annotation in enumerate(raw_annotations):
    initialAnnotation = {
        "id": i + 1,
        "datatorch_id": annotation["id"],
        "datatorch_label_id": annotation["labelId"],
        "image_id": 1,  # There will always only be one file
        "category_id": get_category_id_by_datatorch_label_id(
            categories, annotation["labelId"]
        ),
        "isCrowd": 0,
        "metadata": annotation["metadata"],
    }
    segmentationsAndBbox = generate_segmentation_and_bbox(annotation["sourcesJson"])

    annotations.append({**initialAnnotation, **segmentationsAndBbox})


# Create COCO JSON structure
coco_data = {"categories": categories, "images": images, "annotations": annotations}

set_output("returnText", coco_data)
