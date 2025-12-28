/**
 * Send Release Notification to Discord using Embeds
 *
 * Usage:
 *   node send-discord-release.cjs <type> <webhook-url>
 *
 * Args:
 *   type: 'production' or 'beta'
 *   webhook-url: Discord webhook URL
 */

const fs = require('fs');
const https = require('https');
const { URL } = require('url');

// Parse command line arguments
const releaseType = process.argv[2]; // 'production' or 'beta'
const webhookUrl = process.argv[3];

if (!releaseType || !webhookUrl) {
  console.error('Usage: node send-discord-release.cjs <type> <webhook-url>');
  process.exit(1);
}

// Read CHANGELOG.md and extract the latest release notes
function extractLatestRelease() {
  const changelogPath = 'CHANGELOG.md';

  if (!fs.existsSync(changelogPath)) {
    return {
      version: 'Unknown',
      date: new Date().toISOString().split('T')[0],
      sections: {}
    };
  }

  const content = fs.readFileSync(changelogPath, 'utf8');
  const lines = content.split('\n');

  let version = 'Unknown';
  let date = new Date().toISOString().split('T')[0];
  let collecting = false;
  let currentSection = null;
  const sections = {};

  for (const line of lines) {
    // Match version header: ## 1.15.0 (2025-11-22) or ## [1.15.0](url) (2025-11-22)
    const versionMatch = line.match(/^## \[?(\d+\.\d+\.\d+(?:-beta\.\d+)?)\]?.*?\((\d{4}-\d{2}-\d{2})\)/);
    if (versionMatch) {
      if (!collecting) {
        version = versionMatch[1];
        date = versionMatch[2];
        collecting = true;
        continue;
      } else {
        // Found next version, stop collecting
        break;
      }
    }

    if (!collecting) continue;

    // Match section headers (### Features, ### Bug Fixes, etc.)
    const sectionMatch = line.match(/^### (.+)/);
    if (sectionMatch) {
      currentSection = sectionMatch[1];
      sections[currentSection] = [];
      continue;
    }

    // Collect bullet points
    if (currentSection && line.trim().startsWith('*')) {
      const item = line.trim().substring(1).trim();
      if (item) {
        sections[currentSection].push(item);
      }
    }
  }

  return { version, date, sections };
}

// Create Discord embed
function createEmbed(release) {
  const isBeta = releaseType === 'beta';
  const color = isBeta ? 0xF59E0B : 0x10B981; // Orange for beta, Green for production
  const title = isBeta ? `🧪 Beta Release ${release.version}` : `🚀 Release ${release.version}`;
  const url = `https://github.com/claudekit/claudekit-engineer/releases/tag/v${release.version}`;

  // Map section names to emojis
  const sectionEmojis = {
    'Features': '🚀',
    'Bug Fixes': '🐞',
    'Documentation': '📚',
    'Styles': '💄',
    'Code Refactoring': '♻️',
    'Performance Improvements': '⚡',
    'Tests': '✅',
    'Build System': '🏗️',
    'CI': '👷',
    'Chores': '🔧'
  };

  const fields = [];

  // Add sections as embed fields
  for (const [sectionName, items] of Object.entries(release.sections)) {
    if (items.length === 0) continue;

    const emoji = sectionEmojis[sectionName] || '📌';
    let fieldValue = items.map(item => `• ${item}`).join('\n');

    // Discord field value max is 1024 characters
    if (fieldValue.length > 1024) {
      const truncateAt = fieldValue.lastIndexOf('\n', 1000);
      fieldValue = fieldValue.substring(0, truncateAt) + '\n... *(truncated)*';
    }

    fields.push({
      name: `${emoji} ${sectionName}`,
      value: fieldValue,
      inline: false
    });
  }

  // If no sections found, add a simple message
  if (fields.length === 0) {
    fields.push({
      name: '📋 Release Notes',
      value: 'Release completed successfully. See full changelog on GitHub.',
      inline: false
    });
  }

  const embed = {
    title,
    url,
    color,
    timestamp: new Date().toISOString(),
    footer: {
      text: isBeta ? 'Beta Release • Pre-release' : 'Production Release • Latest'
    },
    fields
  };

  return embed;
}

// Send to Discord
function sendToDiscord(embed) {
  const payload = {
    username: releaseType === 'beta' ? 'Beta Release Bot' : 'Release Bot',
    avatar_url: 'https://github.com/claudekit.png',
    embeds: [embed]
  };

  const url = new URL(webhookUrl);
  const options = {
    hostname: url.hostname,
    path: url.pathname + url.search,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  };

  const req = https.request(options, (res) => {
    let data = '';

    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        console.log('✅ Discord notification sent successfully');
      } else {
        console.error(`❌ Discord webhook failed with status ${res.statusCode}`);
        console.error(data);
        process.exit(1);
      }
    });
  });

  req.on('error', (error) => {
    console.error('❌ Error sending Discord notification:', error);
    process.exit(1);
  });

  req.write(JSON.stringify(payload));
  req.end();
}

// Main execution
try {
  const release = extractLatestRelease();
  console.log(`📦 Preparing ${releaseType} release notification for v${release.version}`);

  const embed = createEmbed(release);
  sendToDiscord(embed);
} catch (error) {
  console.error('❌ Error:', error);
  process.exit(1);
}
