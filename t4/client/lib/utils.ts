import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function calc_remaning(start_date: Date, end_date: Date): string {
  const diff = end_date.getTime() - start_date.getTime();

  if (diff <= 0) {
    return "Finalizado.";
  }

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  const remainingHours = hours % 24;
  const remainingMinutes = minutes % 60;
  const remainingSeconds = seconds % 60;

  let response = "";

  if (days > 0) {
    response += `${days} days, `
  }

  if (remainingHours > 0) {
    response += `${remainingHours} h, `
  }

  if (remainingMinutes > 0) {
    response += `${remainingMinutes} min, `;
  }

  if (remainingSeconds > 0) {
    response += `${remainingSeconds} s`
  }

  return response;
}