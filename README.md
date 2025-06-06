# Schedule 1 Calculator

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Schedule 1 Calculator is a standalone PyQt6 application that helps “Schedule 1” growers in logging/​simulating their in-game mixing and unmixing processes.  

- **Mixing Calculator**: See exactly which “final effects” you get by combining any unlocked base product with any unlocked additives.  
- **Unmixing Calculator**: Given a desired set of effects, find the cheapest sequence of additives—locked to your in-game rank—that achieves them, step by step.  
- **Product Pricing**: Compute real-world cost → sell price based on your own container/soil/enhancer setup (bagged units).  
- **Settings Page**: Customize font, font color, background; toggle rank filtering (display only items you’ve unlocked); enable/disable product pricing.  
- **GitHub Integration**: “Check for Updates” to compare your local version against the latest GitHub release; “Open GitHub” button to view source, report issues, or grab the newest installer.

––––––––––––––––––––––

## Table of Contents

1. [Features](#features)  
2. [Screenshots](#screenshots)  
3. [Installation](#installation)  
4. [Usage](#usage)  
   4.1. [Main Window](#main-window)  
   4.2. [Mixing Calculator](#mixing-calculator)  
   4.3. [Unmixing Calculator](#unmixing-calculator)  
   4.4. [Product Pricing Page](#product-pricing-page)  
   4.5. [Settings](#settings)  
   4.6. [About & Updates](#about--updates)  
5. [Development](#development)  
6. [Packaging into an .exe](#packaging-into-an-exe)  
7. [License](#license)  

---

## Features

- **Mixing Calculator**  
  - Select any unlocked base product (e.g. OG Kush, Sour Diesel) and any combination of unlocked additives.  
  - Preview all resulting effects—before you actually mix.  
  - Step‐by‐step breakdown of how each additive transforms existing effects (visualized in a horizontal “mixing path” widget).

- **Unmixing Calculator**  
  - Choose a base product or let the program **“pick the best one for me.”**  
  - Select up to _N_ desired effects (limit set in Settings).  
  - Runs a breadth‐first search to find a minimal‐cost sequence of additives that produces _all_ chosen effects.  
  - Automatically selects the best weed for your chosen effects if you use **“Pick the best one for me.”**  
  - Displays each additive step, final effect list, total additive cost, and sell price.  
  - Cancel anytime if the search is taking too long.

- **Product Pricing Page**  
  - For each base product tab, choose your growing container, soil, and optional enhancers.  
  - “Calculate” recomputes all product prices (weed, cocaine, meth, etc.) based on your setup and persists them in `data/products.json`.  
  - “Reset” restores worst‐case default settings.  
  - “Disable product prices” hides all base/total‐cost pricing—only additive costs remain.

- **Settings Page**  
  - **Background**: Pick from four built-in images or import your own custom background.  
  - **Font**: Choose any system font (plus built-in “berenika.ttf”).  
  - **Font Color**: Live-preview text color, store it immediately.  
  - **Maximum Effects**: Raise or lower the max number of effects you can pick in “Unmix.”  
  - **Disable Rank Filtering**: If enabled, the program treats you as “highest rank,” unlocking every product/additive. Otherwise, only items at or below your selected in-game rank appear.  
  - **Restore Defaults**: Revert _all_ settings to their original values.

- **About & Update Checker**  
  - Shows an overview of every feature in crisp, professional prose.  
  - Displays your local version number (e.g. 1.0.0).  
  - “Open GitHub” → launches the official GitHub page.  
  - “Check for Updates” → hits GitHub’s REST API for the latest “release,” compares tags, and prompts you if a newer version exists.

---

## Screenshots

![image](https://github.com/user-attachments/assets/c4899389-2c4c-47a2-88fe-775f335b88fc)
![image](https://github.com/user-attachments/assets/339d1a0b-139f-4f25-adef-73b155cd2c7e)
![image](https://github.com/user-attachments/assets/7a75d3b1-c394-4589-9a06-3cb6f786e98b)
![image](https://github.com/user-attachments/assets/3c472214-0a48-4616-9da4-6d91d1751ab5)
![image](https://github.com/user-attachments/assets/5a8d7fbb-315b-4212-86ab-da141d81ca0e)
![image](https://github.com/user-attachments/assets/ea34d4fd-eb59-4039-bbb5-84607d9b5dab)



---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Ccconvict72/Schedule-1-calculator.git
   cd Schedule-1-calculator
