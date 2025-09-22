<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Activity, TrendingUp, Users, Settings, AlertTriangle, Wifi, WifiOff } from 'lucide-svelte';
	import '../app.css';

	// Components
	import Header from '$lib/components/Header.svelte';
	import ControlsRow from '$lib/components/ControlsRow.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import TrafficChart from '$lib/components/TrafficChart.svelte';
	import InterfaceSelector from '$lib/components/InterfaceSelector.svelte';

	// Stores and services
	import {
		interfaces,
		systemStats,
		trafficHistory,
		latestTraffic,
		loadingStates,
		errorStates,
		formattedStats,
		appState,
		api,
		timeControlsState
	} from '$lib/stores/appStore';
	import { initializeOfflineModeManagement, isOfflineMode } from '$lib/services/offlineService';

	// Reactive state from store
	$: selectedTimeRange = $timeControlsState.selectedRange;
	$: selectedGrouping = $timeControlsState.grouping;
	$: realTimeUpdates = $timeControlsState.realTimeUpdates;

	// Calculate theoretical expected data points for display
	function getExpectedDataPoints(timeRange: string, grouping: string): number {
		const intervalMs = getGroupingIntervalMs(grouping);

		switch (timeRange) {
			case '1h': return Math.floor((60 * 60 * 1000) / intervalMs); // 1 hour in ms / interval
			case '6h': return Math.floor((6 * 60 * 60 * 1000) / intervalMs); // 6 hours
			case '24h': return Math.floor((24 * 60 * 60 * 1000) / intervalMs); // 24 hours
			case '7d': return Math.floor((7 * 24 * 60 * 60 * 1000) / intervalMs); // 7 days
			case '30d': return Math.floor((30 * 24 * 60 * 60 * 1000) / intervalMs); // 30 days
			default: return Math.floor((24 * 60 * 60 * 1000) / intervalMs); // Default to 24h
		}
	}

	function getGroupingIntervalMs(grouping: string): number {
		switch (grouping) {
			case '1min': return 1 * 60 * 1000; // 1 minute
			case '5min': return 5 * 60 * 1000; // 5 minutes
			case '15min': return 15 * 60 * 1000; // 15 minutes
			case '1h': return 60 * 60 * 1000; // 1 hour
			case '6h': return 6 * 60 * 60 * 1000; // 6 hours
			case 'auto': return getAutoGroupingInterval(); // Auto-calculate based on time range
			default: return 5 * 60 * 1000; // Default to 5 minutes
		}
	}

	function getAutoGroupingInterval(): number {
		switch (selectedTimeRange) {
			case '1h': return 1 * 60 * 1000; // 1 minute for 1 hour view
			case '6h': return 5 * 60 * 1000; // 5 minutes for 6 hour view
			case '24h': return 15 * 60 * 1000; // 15 minutes for 24 hour view
			case '7d': return 60 * 60 * 1000; // 1 hour for 7 day view
			case '30d': return 6 * 60 * 60 * 1000; // 6 hours for 30 day view
			default: return 5 * 60 * 1000;
		}
	}

	$: expectedDataPoints = getExpectedDataPoints(selectedTimeRange, selectedGrouping);

	// Reactive statements for data
	$: stats = $formattedStats;
	$: trafficData = $latestTraffic;
	$: isLoading = $loadingStates.interfaces || $loadingStates.system || $loadingStates.traffic;
	$: hasErrors = Object.values($errorStates).some(error => error !== null);
	$: loading = isLoading;

	// Event handlers using enhanced API
	async function handleTimeRangeChange(range: '1h' | '6h' | '24h' | '7d' | '30d' | 'custom', customRange?: { start: Date; end: Date }) {
		try {
			await api.timeControls.handleTimeRangeChange(range, customRange);
		} catch (error) {
			console.error('Error handling time range change:', error);
		}
	}

	async function handleGroupingChange(interval: '1min' | '5min' | '15min' | '1h' | '6h' | 'auto') {
		try {
			await api.timeControls.handleGroupingChange(interval);
		} catch (error) {
			console.error('Error handling grouping change:', error);
		}
	}

	async function handleRealTimeToggle() {
		try {
			api.timeControls.toggleRealTimeUpdates();
		} catch (error) {
			console.error('Error toggling real-time updates:', error);
		}
	}

	async function handleRefresh() {
		try {
			await api.refreshAll();
		} catch (error) {
			console.error('Error refreshing data:', error);
		}
	}

	// Initialize data fetching on mount
	onMount(() => {
		// Initialize offline mode management
		initializeOfflineModeManagement();

		// Initialize data fetching
		api.initializeDataFetching();

		// Set up periodic refresh
		const refreshInterval = setInterval(() => {
			if (!$isOfflineMode && realTimeUpdates) {
				api.fetchLatestTraffic();
			}
		}, 30000); // Refresh every 30 seconds

		// Add keyboard shortcuts
		document.addEventListener('keydown', handleKeydown);

		return () => {
			clearInterval(refreshInterval);
			document.removeEventListener('keydown', handleKeydown);
		};
	});

	// Cleanup on destroy
	onDestroy(() => {
		// Cleanup would be handled by the services
	});

	// Keyboard shortcuts
	function handleKeydown(event: KeyboardEvent) {
		// Ctrl/Cmd + R to refresh
		if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
			event.preventDefault();
			handleRefresh();
		}

		// Escape to reset controls
		if (event.key === 'Escape') {
			api.timeControls.resetToDefaults();
		}

		// Space to toggle real-time updates
		if (event.key === ' ') {
			event.preventDefault();
			handleRealTimeToggle();
		}
	}
</script>

<svelte:head>
	<title>Net-Pulse - Network Monitoring Dashboard</title>
	<meta name="description" content="Modern network traffic monitoring dashboard" />
</svelte:head>

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
	<!-- Header -->
	<Header />

	<!-- Main Content -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
		<!-- Page Header -->
		<div class="mb-4 sm:mb-6 lg:mb-8">
			<h2 class="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">Network Dashboard</h2>
			<p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">Monitor your network traffic in real-time</p>
		</div>

		<!-- Interface Selection -->
		<div class="mb-4 sm:mb-6">
			<InterfaceSelector
				placeholder="Select network interfaces to monitor..."
				multiple={true}
				showStats={true}
			/>
		</div>

		<!-- Controls Row -->
		<div class="mb-4 sm:mb-6 lg:mb-8">
			<ControlsRow
				selectedGrouping={selectedGrouping}
				realTimeUpdates={realTimeUpdates}
				onTimeRangeChange={handleTimeRangeChange}
				onGroupingChange={handleGroupingChange}
				onRealTimeToggle={handleRealTimeToggle}
				onRefresh={handleRefresh}
				loading={loading}
			/>
		</div>

		<!-- Error Warning -->
		{#if hasErrors}
			<div class="mb-4 sm:mb-6 p-3 sm:p-4 rounded-lg border-l-4 bg-red-50 border-red-400 dark:bg-red-900/20 dark:border-red-600">
				<div class="flex items-center">
					<AlertTriangle class="w-4 h-4 sm:w-5 sm:h-5 text-red-600 dark:text-red-400 mr-2 sm:mr-3 flex-shrink-0" />
					<div class="flex-1 min-w-0">
						<p class="text-xs sm:text-sm font-medium text-red-800 dark:text-red-200">
							Some data failed to load. Check the console for details.
						</p>
					</div>
				</div>
			</div>
		{/if}

		<!-- Stats Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6 lg:mb-8">
			<StatCard
				title="Active Interfaces"
				value={$interfaces.filter(i => i.status === 'active').length}
				icon="activity"
				color="success"
			/>
			<StatCard
				title="Total Traffic"
				value={stats.totalTraffic}
				icon="trending-up"
				color="primary"
			/>
			<StatCard
				title="CPU Usage"
				value={`${Math.round(stats.cpuUsage)}%`}
				icon="activity"
				color={stats.cpuUsage > 80 ? 'error' : stats.cpuUsage > 60 ? 'warning' : 'success'}
			/>
			<StatCard
				title="Memory Usage"
				value={`${Math.round(stats.memoryUsage)}%`}
				icon="trending-up"
				color={stats.memoryUsage > 80 ? 'error' : stats.memoryUsage > 60 ? 'warning' : 'success'}
			/>
		</div>

		<!-- Traffic Chart -->
		<div class="bg-white dark:bg-slate-800 p-3 sm:p-4 lg:p-6 rounded-lg border border-slate-200 dark:border-slate-700">
			<div class="flex flex-col sm:flex-row sm:items-center justify-between mb-3 sm:mb-4 lg:mb-6 gap-2 sm:gap-0">
				<div class="flex items-center space-x-2 sm:space-x-3 min-w-0">
					<h3 class="text-base sm:text-lg font-semibold text-slate-900 dark:text-white truncate">Traffic Overview</h3>
					{#if $loadingStates.traffic}
						<div class="flex items-center space-x-2 text-slate-500 flex-shrink-0">
							<div class="animate-spin rounded-full h-3 w-3 sm:h-4 sm:w-4 border-b-2 border-primary-600"></div>
							<span class="text-xs sm:text-sm">Loading...</span>
						</div>
					{/if}
					{#if $errorStates.traffic}
						<div class="flex items-center space-x-2 text-red-500 flex-shrink-0">
							<AlertTriangle class="w-3 h-3 sm:w-4 sm:h-4" />
							<span class="text-xs sm:text-sm">Error loading data</span>
						</div>
					{/if}
				</div>
				<div class="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
					<div class="flex items-center space-x-1">
						<div class="w-2 h-2 sm:w-3 sm:h-3 bg-primary-500 rounded-full"></div>
						<span class="text-xs sm:text-sm text-slate-600 dark:text-slate-400">RX Traffic</span>
					</div>
					<div class="flex items-center space-x-1">
						<div class="w-2 h-2 sm:w-3 sm:h-3 bg-teal-500 rounded-full"></div>
						<span class="text-xs sm:text-sm text-slate-600 dark:text-slate-400">TX Traffic</span>
					</div>
					<div class="flex items-center space-x-1 ml-2 sm:ml-3">
						<span class="text-xs sm:text-sm text-slate-500 dark:text-slate-400">•</span>
						<span class="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
							{trafficData.length} data points ({selectedTimeRange})
						</span>
					</div>
				</div>
			</div>
			<TrafficChart
				data={trafficData}
				timeRange={selectedTimeRange === 'custom' ? '24h' : selectedTimeRange}
				grouping={selectedGrouping}
				height={300}
				showLegend={true}
				enableAnimations={true}
				realTimeUpdates={realTimeUpdates}
			/>
		</div>
	</div>
</div>