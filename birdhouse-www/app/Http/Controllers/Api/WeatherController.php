<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Weather;
use Carbon\Carbon;
class WeatherController extends Controller
{
    public function getNow()
    {
        $weather = Weather::orderBy('recorded_at', 'desc')
                          ->limit(1)
                          ->first();
        
        return response()->json($weather);
    }
    
    public function getDaily()
    {
        $weather = Weather::orderBy('recorded_at', 'desc')
                          ->whereBetween('recorded_at', [Carbon::now()->startOfDay(), Carbon::now()])
                          ->get();
    
        return response()->json($weather);
    }

    public function getWeekly()
    {
        $weather = Weather::orderBy('recorded_at', 'desc')
                          ->whereBetween('recorded_at', [Carbon::now()->subDays(7), Carbon::now()])
                          ->get();
    
        return response()->json($weather);
    }
    
    public function getMonthly()
    {
        $weather = Weather::orderBy('recorded_at', 'desc')
                          ->whereBetween('recorded_at', [Carbon::now()->subMonth(), Carbon::now()])
                          ->get();
        
        return response()->json($weather);
    }
    
}