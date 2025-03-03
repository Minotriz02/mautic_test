# Docker para wp api
1. Download image
```sh
docker pull devlikeapro/waha
```
2. Run WhatsApp HTTP API
```sh
docker run -d -p 3000:3000/tcp --name waha devlikeapro/waha
```