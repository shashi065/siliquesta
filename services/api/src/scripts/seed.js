import { prisma } from '../config/database.js';
import AuthService from '../services/authService.js';

async function seed() {
  try {
    console.log('🌱 Seeding database...');

    // Create test users
    const testUser1 = await prisma.user.create({
      data: {
        email: 'test@example.com',
        name: 'Test User',
        password: await AuthService.hashPassword('Test123!@#'),
        role: 'user',
      },
    });

    const testUser2 = await prisma.user.create({
      data: {
        email: 'admin@example.com',
        name: 'Admin User',
        password: await AuthService.hashPassword('Admin123!@#'),
        role: 'admin',
      },
    });

    console.log('✓ Created test users');

    // Create sample projects
    const project1 = await prisma.project.create({
      data: {
        title: 'Thermal Analysis Project',
        description: 'Analyzing heat transfer in complex geometries',
        slug: 'thermal-analysis-project',
        userId: testUser1.id,
        parameters: {
          materialType: 'steel',
          ambientTemp: 25,
        },
        metadata: {
          industry: 'aerospace',
          complexity: 'high',
        },
      },
    });

    const project2 = await prisma.project.create({
      data: {
        title: 'Stress Testing Prototype',
        description: 'FEA simulation for structural integrity',
        slug: 'stress-testing-prototype',
        userId: testUser1.id,
        parameters: {
          loadType: 'distributed',
          maxLoad: 1000,
        },
      },
    });

    console.log('✓ Created sample projects');

    // Create sample simulations
    const simulation1 = await prisma.simulation.create({
      data: {
        title: 'Initial CFD Run',
        description: 'First iteration mesh study',
        status: 'completed',
        input: {
          meshDensity: 0.5,
          flowRate: 100,
        },
        parameters: {
          iterations: 1000,
          tolerance: 0.001,
        },
        output: {
          convergenceAchieved: true,
          finalResidual: 0.0008,
        },
        results: {
          convergence: 0.999,
          error: 0.001,
          accuracy: 0.98,
          iterationsRun: 1000,
        },
        duration: 15000,
        projectId: project1.id,
        userId: testUser1.id,
        completedAt: new Date(),
      },
    });

    const simulation2 = await prisma.simulation.create({
      data: {
        title: 'Parametric Study',
        description: 'Testing different load scenarios',
        status: 'pending',
        input: {
          loadCase: 'symmetric',
          factors: [1, 1.5, 2.0],
        },
        projectId: project2.id,
        userId: testUser1.id,
      },
    });

    console.log('✓ Created sample simulations');

    console.log('✅ Database seeding completed successfully!');
    console.log('\n📋 Test Credentials:');
    console.log('Email: test@example.com');
    console.log('Password: Test123!@#');
    console.log('\nEmail: admin@example.com');
    console.log('Password: Admin123!@#');
  } catch (error) {
    console.error('❌ Error seeding database:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

seed();
