def new_plant_prompt(plant: str) -> tuple[str, list]:
    prompt: str = f"""
    You are an expert in gardening specializing in planting in the mountains of Western
    North Carolina. Provide information about germinating, planting, caring for, and
    harvesting a {plant}
    """

    instructions: list = [
        "Answers should pertain to planting in the mountains of North Carolina above 2800 feet",
        f"Tell us when is the ideal time in the year to plant a {plant}",
        f"Provide information about the best orientation where to plant a {plant}",
        f"Provide information about how much water the {plant} requires",
        f"Provide information about how much sun the {plant} requires",
        f"Provide information about how much shade the {plant} requires",
        f"Provide information about when to harvest the {plant}",
        f"Provide any comments, tips, or recommendations that would be helpful to growing {plant}",
    ]

    return prompt, instructions
