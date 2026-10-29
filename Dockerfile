FROM python:3.12-slim
WORKDIR /app
# CPU-only PyTorch keeps the image far smaller than the default GPU build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
