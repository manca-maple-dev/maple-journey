export const SMART_LINKS = {
  "ask-maple": {
    label: "Ask Maple",
    guestTo: "/features?entry=smart-link&focus=maple-companion",
    memberTo: "/app/chat?entry=smart-link",
  },
  jobs: {
    label: "Jobs",
    guestTo: "/features?entry=smart-link&focus=jobs",
    memberTo: "/app/jobs?entry=smart-link",
    featureKey: "jobs",
  },
  benefits: {
    label: "Benefits",
    guestTo: "/resources?entry=smart-link&topic=benefits",
    memberTo: "/app/benefits?entry=smart-link",
  },
  legal: {
    label: "Legal help",
    guestTo: "/features?entry=smart-link&focus=legal-help",
    memberTo: "/app/legal?entry=smart-link",
    featureKey: "legal",
  },
  connected: {
    label: "Get Connected",
    guestTo: "/features?entry=smart-link&focus=get-connected",
    memberTo: "/app/accessibilities?entry=smart-link",
    featureKey: "accessibilities",
  },
  communities: {
    label: "Communities",
    guestTo: "/features?entry=smart-link&focus=communities",
    memberTo: "/app/communities?entry=smart-link",
    featureKey: "communities",
  },
  "work-permit": {
    label: "Work Permit Help",
    guestTo: "/resources?entry=smart-link&topic=work-permit",
    memberTo: "/app/chat?entry=smart-link&topic=work-permit",
  },
  "study-permit": {
    label: "Study Permit Help",
    guestTo: "/resources?entry=smart-link&topic=study-permit",
    memberTo: "/app/chat?entry=smart-link&topic=study-permit",
  },
  account: {
    guestLabel: "Sign in",
    memberLabel: "Dashboard",
    guestTo: "/login?entry=smart-link",
    memberTo: "/app?entry=smart-link",
  },
  "start-journey": {
    label: "Start your journey",
    guestTo: "/signup?entry=smart-link",
    memberTo: "/app?entry=smart-link",
  },
  "plan-plus": {
    label: "Go Plus",
    guestTo: "/signup?entry=smart-link&intent=plus",
    memberTo: "/app/plans?entry=smart-link&plan=plus",
  },
  "plan-family": {
    label: "Choose Family",
    guestTo: "/signup?entry=smart-link&intent=family",
    memberTo: "/app/plans?entry=smart-link&plan=family",
  },
};

export function resolveSmartLink(key, context = {}) {
  const { isSignedIn = false, features = {} } = context;
  const config = SMART_LINKS[key];

  if (!config) {
    return { label: key, to: "/" };
  }

  const label = isSignedIn ? (config.memberLabel || config.label) : (config.guestLabel || config.label);
  if (!isSignedIn) {
    return { label, to: config.guestTo };
  }

  if (config.featureKey && features[config.featureKey] === false) {
    return { label, to: `/app/plans?entry=smart-link&upgrade=${config.featureKey}` };
  }

  return { label, to: config.memberTo };
}
