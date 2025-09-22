<script lang="ts">
  import { onMount } from 'svelte';
  import { Activity, Settings as SettingsIcon, ArrowLeft } from 'lucide-svelte';
  import Header from '$lib/components/Header.svelte';
  import SettingsModal from '$lib/components/SettingsModal.svelte';

  let showSettingsModal = true;

  function goBack() {
    window.history.back();
  }
</script>

<svelte:head>
  <title>Settings - Net-Pulse</title>
  <meta name="description" content="Configure your network monitoring settings" />
</svelte:head>

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
  <!-- Header -->
  <Header />

  <!-- Main Content -->
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
    <!-- Page Header -->
    <div class="mb-4 sm:mb-6 lg:mb-8">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button
            on:click={goBack}
            class="flex items-center space-x-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            <ArrowLeft class="h-5 w-5" />
            <span class="hidden sm:inline">Back</span>
          </button>
          <div class="flex items-center space-x-3">
            <SettingsIcon class="h-6 w-6 text-primary-600 dark:text-primary-400" />
            <h2 class="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">Settings</h2>
          </div>
        </div>
      </div>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400 mt-2">
        Configure your network monitoring preferences and interface settings
      </p>
    </div>

    <!-- Settings Content -->
    <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 sm:p-6 lg:p-8">
      {#if showSettingsModal}
        <SettingsModal />
      {/if}
    </div>
  </div>
</div>