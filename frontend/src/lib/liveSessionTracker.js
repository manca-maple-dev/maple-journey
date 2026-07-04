import Tracker from '@openreplay/tracker';

let trackerInstance = null;

export function initLiveSessionTracker() {
  const enabled = String(process.env.REACT_APP_ENABLE_LIVE_SESSION_REPLAY || '').toLowerCase() === 'true';
  const projectKey = process.env.REACT_APP_OPENREPLAY_PROJECT_KEY;

  if (!enabled || !projectKey || trackerInstance) {
    return trackerInstance;
  }

  trackerInstance = new Tracker({
    projectKey,
    defaultInputMode: 1,
    obscureTextEmails: true,
    obscureInputNumbers: true,
    captureNetwork: {
      failuresOnly: false,
      sessionTokenHeader: false,
    },
  });

  trackerInstance.start();
  return trackerInstance;
}
