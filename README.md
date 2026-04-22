## Overview

Full-stack web application built with **FastAPI** and **Vue.js**, designed to make image classification model training accessible to professionals from a wide range of non-computing fields.

The platform covers the full workflow, from creating and managing image datasets — including sharing them with other users — to training, evaluating, and running inference with models based on different neural network architectures.

This was my final Bachelor's project and received a grade of **10/10 with highest honors**.

## Main Features

- **Keras** for the machine learning components
- User authentication implemented from scratch with **JWT**, including:
  - Email verification
  - Password recovery
- Model training managed through a queue system using **Celery** and **RabbitMQ**
- **NGINX** as a reverse proxy
- **PostgreSQL** as the database and **SQLModel** as the ORM
- **Docker Compose** for quick and easy deployment
- Deployed on a **DigitalOcean VPS**

## App Architecture
<img width="886" height="420" alt="image" src="https://github.com/user-attachments/assets/5ef996e6-988c-41ac-8eb3-a78c9f6d0054" />
