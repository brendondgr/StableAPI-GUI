import json
import requests

class ImageGenerator():
    def __init__(self):
        self.current_image = "placeholder.jpg"
        self.image_list = ["placeholder.jpg"]
        self.current_image_idx = 0
        with open("keys.json", "r") as f:
            self.api_key = json.load(f)["stable_diffusion"]
        self.model = ""
        self.aspect = ""
        self.seed = ""
        self.use_random_seed = False
        self.prompt = ""
        self.negative_prompt = ""
        self.steps = ""
        self.cfg = ""
        self.samples = ""
        self.use_perplexity = False
        
        # Others
        self.width = ""
        self.height = ""
    
    def set_values(self, api_key, model, aspect, seed, use_random_seed, prompt, negative_prompt, steps, cfg, samples, use_perplexity):
        # Default Values
        self.api_key = api_key
        self.model = model
        self.seed = seed
        self.use_random_seed = use_random_seed
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.steps = steps
        self.cfg = cfg
        self.samples = samples
        self.use_perplexity = use_perplexity

        # Sets up the proper widths and heights for the different models
        if model == "stable-diffusion-v1-6":
            self.aspect = aspect.split(" | ")[2]
            self.width = aspect.split(" | ")[2].split("x")[0]
            self.height = aspect.split(" | ")[2].split("x")[1]
        elif model == "stable-diffusion-xl-1024-v1-0":
            self.aspect = aspect.split(" | ")[1]
            self.width = aspect.split(" | ")[1].split("x")[0]
            self.height = aspect.split(" | ")[1].split("x")[1]
        elif model in ["stable-diffusion-3-large", "stable-diffusion-3-large-turbo", "stable-diffusion-3-medium", "stable-diffusion-3-5-large", "stable-diffusion-3-5-large-turbo", "stable-diffusion-3-5-medium"]:
            self.aspect = aspect.split(" | ")[0]
            self.width = aspect.split(" | ")[0].split("x")[0]
            self.height = aspect.split(" | ")[0].split("x")[1]
            
    
    def generate_image(self):
        # Generate prompt based on perplexity
        if self.use_perplexity:
            self.prompt = promptPPLX(self.prompt)

        # Generate seed if random seed is enabled
        if self.use_random_seed:
            from random import randint
            self.seed = randint(0, 4294967295)
        
        # Generate image based on model
        if self.model in ["stable-diffusion-3-large", "stable-diffusion-3-large-turbo", "stable-diffusion-3-medium", "stable-diffusion-3-5-large", "stable-diffusion-3-5-large-turbo", "stable-diffusion-3-5-medium"]:
            response = generate_stable3(self.api_key, self.prompt, model=self.model, aspect_ratio=self.aspect, negative_prompt=self.negative_prompt, seed=self.seed)
        if self.model == "stable-diffusion-v1-6" or self.model == "stable-diffusion-xl-1024-v1-0":
            response = generate_nonstable3(self.api_key, self.prompt, engine_id=self.model, cfg=self.cfg, height=self.height, width=self.width, samples=self.samples, steps=self.steps, use_seed=self.use_random_seed, seed_val=self.seed)
        
        # Save images to folder
        locations = saveimages(response, self.model)
        
        # Change current picture to the first image in the list
        if len(locations) == 1:
            self.current_image = locations[0]
            self.image_list = locations
            self.current_image_idx = 0
        else:
            self.current_image = locations[0]
            self.image_list = locations
            self.current_image_idx = 0
        
def possibleSamplers():
    return ['DDIM', 'DDPM', 'K_DPMPP_2M', 'K_DPMPP_2S_ANCESTRAL',
            'K_DPM_2', 'K_DPM_2_ANCESTRAL', 'K_EULER', 'K_EULER_ANCESTRAL',
            'K_HEUN', 'K_LMS']

def createFolders(pathloc):
    from os import mkdir, path
    # Retrieves path in format: './folder1/folder2/folder3'
    folders = pathloc.split('/')

    # Go down the path and create folders if they don't exist
    for i in range(1, len(folders)):
        folder = '/'.join(folders[:i+1])
        if not path.exists(folder): mkdir(folder)
        
def generate_nonstable3(api_key, prompt, engine_id='stable-diffusion-xl-1024-v1-0', cfg=7, height=1024, width=1024, samples=1, steps=30, use_seed=False, seed_val=0):
    from os import getenv
    from requests import post
    
    api_host = getenv('API_HOST', 'https://api.stability.ai')
    response = post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": f"{prompt}"
                }
            ],
            "cfg_scale": int(cfg),
            "height": int(height),
            "width": int(width),
            "samples": int(samples),
            "steps": int(steps),
            "seed": int(seed_val),
        },
    )

    return response

def generate_stable3(api_key, prompt, model, strength=0.5, aspect_ratio='1:1', seed=0, negative_prompt='', cfg_scale=7):
    from os import getenv
    from requests import post
    
    api_host = getenv('API_HOST', 'https://api.stability.ai')
    
    # Prepare the request payload
    payload = {
        "text_prompts": [
            {"text": prompt}
        ],
        "cfg_scale": cfg_scale,
        "aspect_ratio": aspect_ratio,
        "strength": strength,
        "seed": seed if seed != 0 else None,
    }
    
    # Exclude negative_prompt for sd3-large-turbo
    if model != "stable-diffusion-3-large-turbo":
        payload["negative_prompt"] = negative_prompt

    # Make the API request
    response = post(
        f"{api_host}/v1/generation/{model}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json=payload
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    return response

def saveimages(data, model):
    from time import strftime
    from base64 import b64decode
    
    # Retrieve current time in format, hours_minutes_seconds
    current_time = strftime("%H%M%S")

    # Retrieve current date in format, year-month-day
    current_date = strftime("%Y-%m-%d")

    # Output Folder Path
    output_folder = f"./images/{current_date}"

    createFolders(output_folder)
    
    if data.status_code != 200:
        raise Exception("Non-200 response: " + str(data.text))

    # List of image locations
    imagelocs = []
    
    if model == "sd3-turbo" or model == "sd3":
        image = data.content
        with open(f'{output_folder}/{current_time}.png', "wb") as f:
            f.write(image)
            name = f'{output_folder}/{current_time}.png'
            imagelocs.append(name)
            
    elif model == "stable-diffusion-v1-6" or model == "stable-diffusion-xl-1024-v1-0":
        data = data.json()
        for i, image in enumerate(data["artifacts"]):
            with open(f'{output_folder}/{current_time}_{i}.png', "wb") as f:
                f.write(b64decode(image["base64"]))
                name = f'{output_folder}/{current_time}_{i}.png'
                imagelocs.append(name)
            
    return imagelocs

def displayimages(data):
    import matplotlib.pyplot as plt
    
    # Data is a list of file locations. Display each image in matplotlib.
    # If more than one image, display in a grid, at most 2 images per row

def promptPPLX(query):
    # Load the API key from the keys.json file, key "perplexity"
    with open("keys.json", "r") as f:
        keys = json.load(f)
        token = keys["perplexity"]
    
    url = "https://api.perplexity.ai/chat/completions"

    try:
        payload = {
            "model": f"sonar",
            "messages": [
                {
                    "role": "system",
                    "content": f'''Limiting your response to 50 words, act as a creative agent who generates a very terse but highly creative image prompt derived from the prompt I send you.  Include descriptive visual elements of the subject, lighting and surroundings.  Specify an artistic style or camera settings at the beginning of the sentence, using descriptive elements that pertain to this artistic style.  Include no more than 10 elements presented as discrete descriptors in one long sentence without story.  Put the most important descriptive elements at the beginning of the sentence. Here are 6 example prompts that should serve as a template for text to image prompts that I ask you to create.


    Surrealist painting: Adorable puppies frolicking in a tempestuous sea of mewing kittens, surrounded by gargantuan, glistening ice cubes. Soft, warm lighting illuminates the fantastical scene, emphasizing the contrasting textures of fur and frost. Vivid colors swirl in a dreamlike atmosphere, capturing the playful energy of the impossible scenario.

    Vibrant 3D Pixar style render, neon-lit forest, adorable squinting animals, oversized gummy sword, water balloon gun, exaggerated mock duel, hilarious facial expressions, dynamic action poses, volumetric lighting, depth of field.

    Vibrant digital art, dynamic lighting: Elderly grandmother with mischievous grin piloting unique mecha suit made of large, colorful speakers, blasting blue sound waves at unsuspecting people, bustling cityscape background with mix of modern and vintage buildings, lively atmosphere.

    Neon-lit microscopic view: Colorful anthropomorphic bacteria, viruses, and microbes dancing wildly on a glowing Petri dish dance floor, surrounded by pulsating organelles, with a DJ microbe spinning records on a DNA turntable, while microscope lasers create a dazzling light show overhead.

    Please create an image prompt for:
    {query}
                    '''
                },
                    {
                        "role": "user",
                        "content": f'{query}'
                    }        ],
            "max_tokens": 2000,
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {token}"
        }
    except:
        # Print Error...
        print("Error in Perplexity Response. Please check the API key.")
        return query
        
    # Parse
    response = (requests.post(url, json=payload, headers=headers)).text
    
    # Parses the data from the API response.
    try:
        parsed_data = json.loads(response)
        content = parsed_data["choices"][0]["message"]["content"]
        return [content][0]
    except:
        # Return Original Prompt.
        return query