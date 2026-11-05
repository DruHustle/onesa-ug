FROM node:24.22.1-alpine
WORKDIR /recovery
COPY --chown=node:node scripts/backup-lib.mjs scripts/backup.mjs scripts/restore.mjs ./
USER node
ENTRYPOINT ["node"]
CMD ["backup.mjs", "--help"]
