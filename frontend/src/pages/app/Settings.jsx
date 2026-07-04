import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Settings, Download, Trash2, Lock, LogOut, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import api, { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export default function AccountSettings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleExportData = async () => {
    setExporting(true);
    try {
      const response = await api.get("/auth/export", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `maple-data-export-${new Date().toISOString().split("T")[0]}.json`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      toast.success("Your data has been exported");
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setExporting(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setChangingPassword(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success("Password changed successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") {
      toast.error('Please type "DELETE" to confirm');
      return;
    }

    setDeleting(true);
    try {
      await api.delete("/auth/account");
      toast.success("Account deleted. Goodbye!");
      setTimeout(() => {
        logout();
        navigate("/");
      }, 1000);
    } catch (err) {
      toast.error(apiError(err));
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold flex items-center gap-2">
          <Settings className="h-8 w-8 text-maple-red" />
          Account Settings
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your account, security, and preferences.
        </p>
      </div>

      {/* Appearance */}
      <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
        <div>
          <h2 className="font-semibold text-lg">Appearance</h2>
          <p className="text-sm text-muted-foreground">Customize how the app looks.</p>
        </div>

        <div className="space-y-3 border-t border-border pt-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="dark-mode">Dark mode</Label>
            <Switch
              id="dark-mode"
              checked={theme === "dark"}
              onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
            />
          </div>
          <div className="text-sm text-muted-foreground">
            {theme === "dark" ? "Dark mode is enabled" : "Dark mode is disabled"}
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
        <div>
          <h2 className="font-semibold text-lg flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Security
          </h2>
          <p className="text-sm text-muted-foreground">Update your password and security settings.</p>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4 border-t border-border pt-4">
          <div>
            <Label htmlFor="current-pwd">Current Password</Label>
            <Input
              id="current-pwd"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter your current password"
              className="mt-2"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="new-pwd">New Password</Label>
              <Input
                id="new-pwd"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="confirm-pwd">Confirm Password</Label>
              <Input
                id="confirm-pwd"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter new password"
                className="mt-2"
              />
            </div>
          </div>

          <Button type="submit" disabled={changingPassword || !currentPassword || !newPassword}>
            {changingPassword && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Update Password
          </Button>
        </form>
      </div>

      {/* Data & Privacy */}
      <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
        <div>
          <h2 className="font-semibold text-lg flex items-center gap-2">
            <Download className="h-5 w-5" />
            Data & Privacy
          </h2>
          <p className="text-sm text-muted-foreground">
            Download your personal data or delete your account.
          </p>
        </div>

        <div className="space-y-4 border-t border-border pt-4">
          {/* Export Data */}
          <div>
            <h3 className="font-medium mb-2">Export Your Data</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Download a copy of all your personal information, profile data, and history as a JSON file.
              This complies with PIPEDA data subject rights.
            </p>
            <Button
              variant="outline"
              onClick={handleExportData}
              disabled={exporting}
              className="w-full sm:w-auto"
            >
              {exporting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <Download className="h-4 w-4 mr-2" />
              Download Data
            </Button>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="rounded-2xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950 p-6 space-y-4">
        <div>
          <h2 className="font-semibold text-lg flex items-center gap-2 text-red-600 dark:text-red-400">
            <AlertCircle className="h-5 w-5" />
            Danger Zone
          </h2>
          <p className="text-sm text-red-600 dark:text-red-300 mt-1">
            Irreversible actions. Proceed with caution.
          </p>
        </div>

        <div className="space-y-4 border-t border-red-200 dark:border-red-900 pt-4">
          {/* Delete Account */}
          <div>
            <h3 className="font-medium text-red-700 dark:text-red-300 mb-2">Delete Account</h3>
            <p className="text-sm text-red-600 dark:text-red-400 mb-4">
              Deleting your account is permanent. All your data will be erased within 30 days.
              This cannot be undone.
            </p>

            {!showDeleteConfirm ? (
              <Button
                variant="destructive"
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full sm:w-auto"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete My Account
              </Button>
            ) : (
              <div className="space-y-3 p-4 rounded-lg bg-white dark:bg-slate-950 border border-red-300 dark:border-red-800">
                <div>
                  <Label htmlFor="confirm-delete" className="text-red-700 dark:text-red-300">
                    Type "DELETE" to confirm permanent deletion:
                  </Label>
                  <Input
                    id="confirm-delete"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value.toUpperCase())}
                    placeholder="Type DELETE"
                    className="mt-2 font-mono uppercase"
                  />
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    onClick={handleDeleteAccount}
                    disabled={deleting || deleteConfirmText !== "DELETE"}
                  >
                    {deleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    Yes, Delete Permanently
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setDeleteConfirmText("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Logout */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <Button
          variant="outline"
          onClick={() => {
            logout();
            navigate("/");
          }}
          className="w-full sm:w-auto"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Log Out
        </Button>
      </div>
    </div>
  );
}
