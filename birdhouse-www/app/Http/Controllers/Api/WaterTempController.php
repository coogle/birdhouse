<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\WaterTemp;
use Carbon\Carbon;
class WaterTempController extends Controller
{
    public function getNow()
    {
        $waterTemp = WaterTemp::orderBy('recorded_at', 'desc')
                              ->limit(1)
                              ->first();
        
        return response()->json($waterTemp);
    }
    
    public function getDaily()
    {
        $waterTemp = WaterTemp::orderBy('recorded_at', 'desc')
                              ->whereBetween('recorded_at', [Carbon::now()->startOfDay(), Carbon::now()])
                              ->get();
        
        return response()->json($waterTemp);
    }
    
    public function getWeekly()
    {
        $waterTemp = WaterTemp::orderBy('recorded_at', 'desc')
                              ->whereBetween('recorded_at', [Carbon::now()->subDays(7)->startOfDay(), Carbon::now()])
                              ->get();
    
        return response()->json($waterTemp);
    }
    
    public function getMonthly()
    {
        $waterTemp = WaterTemp::orderBy('recorded_at', 'desc')
                              ->whereBetween('recorded_at', [Carbon::now()->subMonth(1)->startOfDay(), Carbon::now()])
                              ->get();
    
        return response()->json($waterTemp);
    }
}