FROM node:12

COPY . /sandbox

WORKDIR /sandbox

RUN npm install --only=production

USER nobody

CMD ["node", "index.js"]
