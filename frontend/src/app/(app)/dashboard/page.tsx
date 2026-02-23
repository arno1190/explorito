"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { childrenApi, gamificationApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Play, TrendingUp } from "lucide-react";
import type { Child, GamificationStats } from "@/types";

export default function DashboardPage() {
  const { user, impersonateChild } = useAuth();
  const [children, setChildren] = useState<Child[]>([]);
  const [childrenStats, setChildrenStats] = useState<
    Record<string, GamificationStats>
  >({});
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      setLoading(true);
      const data = await childrenApi.getAll();
      setChildren(data);

      // Load stats for each child
      const statsPromises = data.map(async (child) => {
        try {
          const stats = await gamificationApi.getStats(child.id);
          return { id: child.id, stats };
        } catch (err) {
          console.error(`Failed to load stats for child ${child.id}:`, err);
          return { id: child.id, stats: null };
        }
      });

      const statsResults = await Promise.all(statsPromises);
      const statsMap: Record<string, GamificationStats> = {};
      statsResults.forEach(({ id, stats }) => {
        if (stats) {
          statsMap[id] = stats;
        }
      });
      setChildrenStats(statsMap);
    } catch (err) {
      console.error("Failed to load children:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddChild = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await childrenApi.create({
        name,
        birth_date: birthDate,
        email,
        password,
      });
      setDialogOpen(false);
      setName("");
      setBirthDate("");
      setEmail("");
      setPassword("");
      loadChildren();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to add child. Please try again."
      );
    }
  };

  const handleDeleteChild = async (id: string) => {
    if (!confirm("Are you sure you want to delete this child?")) {
      return;
    }

    try {
      await childrenApi.delete(id);
      loadChildren();
    } catch (err) {
      console.error("Failed to delete child:", err);
    }
  };

  const calculateAge = (birthDate: string) => {
    const today = new Date();
    const birth = new Date(birthDate);
    const months = Math.floor(
      (today.getTime() - birth.getTime()) / (1000 * 60 * 60 * 24 * 30.44)
    );
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;

    if (years === 0) {
      return `${months} months`;
    }
    return `${years} year${years > 1 ? "s" : ""} ${remainingMonths} month${remainingMonths !== 1 ? "s" : ""}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Welcome, {user?.profile?.display_name || "User"}!
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage your children and discover age-appropriate activities
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Child
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={handleAddChild}>
              <DialogHeader>
                <DialogTitle>Add a new child</DialogTitle>
                <DialogDescription>
                  Add your child's information to get personalized activity
                  recommendations
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {error && (
                  <div className="bg-fun-red-light text-fun-red p-3 rounded-xl text-sm">
                    {error}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="birthDate">Birth Date</Label>
                  <Input
                    id="birthDate"
                    type="date"
                    value={birthDate}
                    onChange={(e) => setBirthDate(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Add Child</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
        </div>
      ) : children.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">
              You haven't added any children yet.
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add your first child
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {children.map((child) => {
            const stats = childrenStats[child.id];
            return (
              <Card key={child.id} className="overflow-hidden candy-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{child.name}</CardTitle>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteChild(child.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                  <CardDescription>
                    Age: {calculateAge(child.birth_date)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Stats Display */}
                  {stats && (
                    <div className="grid grid-cols-2 gap-2 py-3 px-2 bg-muted rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-fun-sun">
                          ⚡ {stats.total_xp}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          XP Total
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-fun-sun">
                          🔥 {stats.current_streak}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Jours
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Progress bar */}
                  {stats && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Niveau {stats.level}</span>
                        <span>
                          {stats.current_level_xp} / {stats.next_level_xp} XP
                        </span>
                      </div>
                      <div className="w-full bg-fun-green-light rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-fun-green to-fun-sky h-2 rounded-full transition-all"
                          style={{
                            width: `${(stats.current_level_xp / stats.next_level_xp) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="space-y-2 pt-2">
                    <Button
                      className="w-full"
                      onClick={() => impersonateChild(child)}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      Jouer comme {child.name}
                    </Button>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => {
                        // TODO: Navigate to progress view
                        console.log("View progress for", child.id);
                      }}
                    >
                      <TrendingUp className="mr-2 h-4 w-4" />
                      Voir les progrès
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
