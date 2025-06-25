# ---------- Full Runtime Container ----------
FROM node:18

# Install Python
RUN apt update && apt install -y python3 python3-pip

# Set working directory
WORKDIR /app

# Copy only backend requirements first and install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy backend source files except webapp
COPY . . 
# Note: webapp folder files will be copied separately below

# Setup frontend: copy package files separately for better cache and install node deps
WORKDIR /app/webapp
COPY webapp/package*.json ./

RUN npm install

# Now copy rest of frontend files
COPY webapp/. .

RUN npm run build

# Back to main working directory
WORKDIR /app

# Expose backend and frontend ports
EXPOSE 8000
EXPOSE 5173

# Start backend and frontend (entrypoint.sh)
CMD ["bash", "entrypoint.sh"]
