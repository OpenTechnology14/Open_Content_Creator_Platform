FROM python:3.11-slim

WORKDIR /app

# No apt-get step. opencv-python-headless (requirements.txt) links against no
# GL/X11/GTK libraries, unlike the standard opencv-python wheel this Dockerfile
# used to install alongside libgl1-mesa-glx + libglib2.0-0. That package name
# was removed from Debian's current apt repo (python:3.11-slim tracks a moving
# base image) and broke every build; -headless removes the dependency instead
# of chasing the renamed package. This exporter never calls cv2's GUI
# functions (imshow etc.) — only VideoCapture, present in both builds.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9101

CMD ["python", "exporter.py"]
