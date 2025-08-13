# Food Waste Management System  

[**Live Demo on Streamlit**](https://foodwastagemanagement.streamlit.app)  

## 📌 Overview  
The **Food Waste Management System** is an interactive application designed to connect **food providers** (restaurants, grocery stores, etc.) with **food receivers** (charities, shelters, etc.) to minimize food wastage.  
---

The platform allows users to:  
- Browse available food donations by **location, provider type, and food type**.  
- Contact providers and receivers directly from the app.  
- Perform **CRUD operations** (Create, Read, Update, Delete) on database records.  
- View **15 SQL queries** with data visualizations for insights.  
---

## 📂 Features  
✅ **Dataset loading** from CSV files  
✅ **SQLite database creation** (`food_management.db`) with 4 main tables:  
- Providers  
- Receivers  
- Food Listings  
- Claims

✅ **CRUD operations** to manage records  
✅ **Data analysis & visualization** using SQL queries and charts  
✅ **Streamlit UI** for interactive filtering, searching, and data entry

---

## 📊 Technologies Used  
- **Python**  
- **SQLite3** for database management  
- **Pandas** for data handling  
- **Matplotlib & Seaborn** for data visualization  
- **Streamlit** for the web interface  
---

## 🚀 How to Run Locally  

1. **Clone the repository**
  git clone https://github.com/yourusername/food_waste_management.git
  cd food_waste_management

2. Install dependencies
  pip install -r requirements.txt

3. Run Streamlit app
  streamlit run app.py
---

| File                                   | Description                     |
| -------------------------------------- | ------------------------------- |
| `app.py`                               | Main Streamlit application file |
| `food_management.db`                   | SQLite database                 |
| `providers_data.csv`                   | Providers dataset               |
| `receivers_data.csv`                   | Receivers dataset               |
| `food_listings_data.csv`               | Food listings dataset           |
| `claims_data.csv`                      | Claims dataset                  |
| `requirements.txt`                     | Python dependencies             |
| `Food_Wastage_Management_System.ipynb` | Jupyter Notebook for analysis   |
| `README.md`                            | Project documentation           |

---

📈 Key Insights from Analysis
Identified top contributing food providers by type.

Found cities with the most active providers and receivers.

Analyzed claim completion rates to identify operational gaps.

Discovered most common food and meal types being donated and claimed.

---

👤 Author

 [Alwin Shaji](https://linkedin.com/in/alwin-shaji)



