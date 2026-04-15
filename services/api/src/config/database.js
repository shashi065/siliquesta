import { PrismaClient } from '@prisma/client';
import dotenv from 'dotenv';

dotenv.config();

// Instantiate Prisma Client
export const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development' 
    ? ['query', 'info', 'warn', 'error']
    : ['warn', 'error'],
  errorFormat: 'pretty',
});

export default prisma;
