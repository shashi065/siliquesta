import express from 'express';
import { authenticate } from '../middleware/auth.js';
import { prisma } from '../config/database.js';
import { getPlanPayload } from '../services/subscriptionService.js';

const router = express.Router();

router.get('/user/plan', authenticate, async (req, res, next) => {
  try {
    res.status(200).json(await getPlanPayload(req.user.userId));
  } catch (error) {
    next(error);
  }
});

router.post('/team/create', authenticate, async (req, res, next) => {
  try {
    const ownerId = req.user.userId;
    const name = String(req.body?.name || 'Siliquesta Team').trim();
    const user = await prisma.user.findUnique({ where: { id: ownerId } });

    const team = await prisma.team.create({
      data: {
        name,
        ownerId,
        members: {
          create: {
            userId: ownerId,
            email: user?.email || req.user.email || 'owner@siliquesta.local',
            role: 'owner',
            status: 'active',
          },
        },
      },
      include: { members: true },
    });

    res.status(201).json({ team });
  } catch (error) {
    next(error);
  }
});

router.post('/team/invite', authenticate, async (req, res, next) => {
  try {
    const email = String(req.body?.email || '').trim().toLowerCase();
    if (!email || !email.includes('@')) {
      return res.status(400).json({ message: 'Valid email is required' });
    }

    let team = await prisma.team.findFirst({
      where: { ownerId: req.user.userId },
      orderBy: { createdAt: 'desc' },
    });

    if (!team) {
      team = await prisma.team.create({
        data: {
          name: 'Siliquesta Team',
          ownerId: req.user.userId,
        },
      });
    }

    const existingUser = await prisma.user.findUnique({ where: { email } });
    const member = await prisma.teamMember.create({
      data: {
        teamId: team.id,
        userId: existingUser?.id,
        email,
        role: 'member',
        status: existingUser ? 'active' : 'invited',
      },
    });

    res.status(201).json({ team_id: team.id, member });
  } catch (error) {
    next(error);
  }
});

router.get('/team/members', authenticate, async (req, res, next) => {
  try {
    const ownedTeams = await prisma.team.findMany({
      where: { ownerId: req.user.userId },
      select: { id: true },
    });
    const ownedTeamIds = ownedTeams.map((team) => team.id);
    const memberships = await prisma.teamMember.findMany({
      where: {
        OR: [
          { userId: req.user.userId },
          { teamId: { in: ownedTeamIds } },
        ],
      },
      include: { team: true },
      orderBy: { createdAt: 'asc' },
    });

    res.status(200).json({ members: memberships });
  } catch (error) {
    next(error);
  }
});

router.post('/export/report', authenticate, async (req, res, next) => {
  try {
    const results = req.body?.results || {};
    const project = req.body?.project || 'SILIQUESTA optimization run';
    const confidence = results.confidence ?? req.body?.confidence ?? null;
    const improvement = Number(results.improvement_percent || 0).toFixed(1);

    res.status(200).json({
      project,
      results,
      timestamp: new Date().toISOString(),
      confidence,
      summary: `AI optimized design reduced weighted objective by ${improvement}%.`,
    });
  } catch (error) {
    next(error);
  }
});

router.post('/stripe/create-checkout-session', authenticate, async (req, res) => {
  const checkoutUrl = process.env.STRIPE_CHECKOUT_URL || process.env.STRIPE_PRO_CHECKOUT_URL;

  if (!checkoutUrl) {
    return res.status(503).json({
      message: 'Stripe checkout is not configured yet. Set STRIPE_CHECKOUT_URL on the backend.',
    });
  }

  res.status(200).json({
    url: checkoutUrl,
    plan: req.body?.plan || 'pro',
  });
});

export default router;
