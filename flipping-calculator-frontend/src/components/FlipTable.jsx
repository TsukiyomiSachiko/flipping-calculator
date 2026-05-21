import React, { useState, useMemo, useCallback } from 'react';
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import { formatGP, formatExactGP, formatPercent, getVolumeIndicator } from '../utils/formatters';

const FlipTable = React.memo(function FlipTable({ flips, onSelectFlip, onShowDetail }) {
  const [expandedRows, setExpandedRows] = useState({});

  // ⚡ Bolt: wrap in useCallback to prevent DesktopTable re-rendering unnecessarily
  const toggleRow = useCallback((rowId) => {
    setExpandedRows((prev) => ({
      ...prev,
      [rowId]: !prev[rowId],
    }));
  }, []);

  if (!flips || flips.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-400">No flips found. Try adjusting your filters.</p>
      </div>
    );
  }

  return (
    <>
      {/* Mobile: Card layout */}
      <div className="md:hidden space-y-2">
        {flips.map((item, idx) => {
          const isExpanded = expandedRows[idx];
          const scoreColor = item.score >= 70 ? 'text-osrs-green' :
                            item.score >= 45 ? 'text-yellow-400' :
                            item.score >= 25 ? 'text-orange-400' : 'text-gray-400';

          return (
            <div key={item.id} className="card p-0 overflow-hidden">
              {/* Collapsed: Name + Score + Chevron */}
              <button
                className="w-full flex items-center justify-between p-4 text-left"
                onClick={() => toggleRow(idx)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <button
                    className="font-medium text-osrs-gold truncate cursor-pointer hover:text-yellow-400 bg-transparent border-0 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('Item clicked:', item.name, 'Handler:', typeof onShowDetail);
                      if (onShowDetail) {
                        onShowDetail(item);
                      } else {
                        console.error('onShowDetail is not defined!');
                      }
                    }}
                  >
                    {item.name}
                  </button>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`font-bold ${scoreColor}`}>{item.score ?? '—'}</span>
                  <span className={`text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}>
                    ›
                  </span>
                </div>
              </button>

              {/* Expanded: All data */}
              {isExpanded && (
                <div className="border-t border-gray-700 px-4 pb-4">
                  {/* Key metrics */}
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    <MobileField label="Buy Price" value={formatExactGP(item.buy_price)} color="text-osrs-red" />
                    <MobileField label="Sell Price" value={formatExactGP(item.sell_price)} color="text-osrs-green" />
                    <MobileField label="Profit" value={formatGP(item.profit)} color="text-osrs-gold" />
                    <MobileField label="ROI" value={formatPercent(item.roi)} color={
                      item.roi >= 10 ? 'text-osrs-green' : item.roi >= 5 ? 'text-yellow-400' : 'text-gray-400'
                    } />
                    <MobileField label="Limit Profit" value={formatGP(item.limit_profit)} color="text-blue-400" />
                    <MobileField label="Volume" value={
                      (() => { const v = getVolumeIndicator(item.volume); return `${v.emoji} ${item.volume?.toLocaleString() || 'N/A'}`; })()
                    } />
                    <MobileField label="GE Limit" value={item.ge_limit?.toLocaleString() || 'N/A'} />
                    <MobileField label="Score" value={`${item.score ?? '—'} / 100`} color={scoreColor} />
                    <MobileField label="Risk-Adj Score" value={item.risk_adjusted_score != null ? `${item.risk_adjusted_score.toFixed(1)} / 100` : '—'} color={
                      item.risk_adjusted_score >= 70 ? 'text-osrs-green' :
                      item.risk_adjusted_score >= 45 ? 'text-yellow-400' :
                      item.risk_adjusted_score >= 25 ? 'text-orange-400' : 'text-gray-400'
                    } />
                    <MobileField label="Crash Risk" value={item.crash_risk_score != null ? `${item.crash_risk_score.toFixed(0)} / 100` : '—'} color={
                      item.crash_risk_score == null ? 'text-gray-500' :
                      item.crash_risk_score < 35 ? 'text-osrs-green' :
                      item.crash_risk_score <= 70 ? 'text-yellow-400' : 'text-osrs-red'
                    } />
                    <MobileField label="Max Drawdown (30d)" value={item.max_drawdown_30d != null ? `${item.max_drawdown_30d.toFixed(1)}%` : '—'} color="text-osrs-red" />
                    <MobileField label="Price Percentile" value={item.price_percentile_30d != null ? `${item.price_percentile_30d.toFixed(1)}%` : '—'} />
                    <MobileField label="Risk-to-Reward" value={item.risk_to_reward_ratio != null ? `${item.risk_to_reward_ratio.toFixed(2)}x` : '—'} color={
                      item.risk_to_reward_ratio == null ? 'text-gray-500' :
                      item.risk_to_reward_ratio > 3 ? 'text-osrs-red' :
                      item.risk_to_reward_ratio > 1.5 ? 'text-yellow-400' : 'text-osrs-green'
                    } />
                    <MobileField label="Your Profit" value={formatGP(item.your_profit)} color="text-osrs-green" />
                    <MobileField label="Max Qty" value={item.max_qty?.toLocaleString() || 'N/A'} />
                    <MobileField label="Members" value={item.members ? '⭐ Members' : 'F2P'} />
                    <MobileField label="GE Tax" value={
                      item.sell_price > 50 ? formatGP(Math.floor(item.sell_price * 0.02)) : '0 gp'
                    } color="text-osrs-red" />
                    {item.secondary_score != null && (
                      <MobileField label="Erebus Score" value={item.secondary_score} color={
                        item.secondary_score >= 50 ? 'text-purple-400' :
                        item.secondary_score >= 20 ? 'text-osrs-green' :
                        item.secondary_score >= 5 ? 'text-yellow-400' : 'text-gray-400'
                      } />
                    )}
                    <div className="col-span-2">
                      <p className="text-xs text-gray-400 mb-1">Data Quality</p>
                      <p className={`font-bold ${
                        item.quality_score == null ? 'text-gray-500' :
                        item.quality_score >= 80 ? 'text-osrs-green' :
                        item.quality_score >= 50 ? 'text-yellow-400' : 'text-osrs-red'
                      }`}>
                        {item.quality_score != null ? `${item.quality_score.toFixed(0)} / 100` : '—'}
                        {item.quality_flags?.length > 0 && (
                          <span className="text-xs block text-orange-400 mt-1">
                            ⚠ {item.quality_flags[0]}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  {/* Exact prices */}
                  <div className="mt-3 text-xs text-gray-500 space-y-1">
                    <p>Buy: {item.buy_price?.toLocaleString()} gp · Sell: {item.sell_price?.toLocaleString()} gp · Profit: {item.profit?.toLocaleString()} gp</p>
                  </div>

                  {/* Buy button */}
                  <button
                    className="btn btn-primary w-full mt-3 text-sm py-2"
                    onClick={() => onSelectFlip(item)}
                  >
                    Buy
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Desktop: Table layout */}
      <DesktopTable
        flips={flips}
        expandedRows={expandedRows}
        toggleRow={toggleRow}
        onSelectFlip={onSelectFlip}
        onShowDetail={onShowDetail}
      />
    </>
  );
});

const MobileField = React.memo(function MobileField({ label, value, color = 'text-white' }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className={`font-medium text-sm ${color}`}>{value}</p>
    </div>
  );
});

const DesktopTable = React.memo(function DesktopTable({ flips, expandedRows, toggleRow, onSelectFlip, onShowDetail }) {
  const columns = useMemo(
    () => [
      {
        header: 'Item',
        accessorKey: 'name',
        cell: ({ row }) => (
          <button
            className="font-medium text-osrs-gold hover:text-yellow-300 text-left transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              console.log('Desktop item clicked:', row.original.name, 'Handler:', typeof onShowDetail);
              if (onShowDetail) {
                onShowDetail(row.original);
              } else {
                console.error('onShowDetail is not defined!');
              }
            }}
          >
            {row.original.name}
          </button>
        ),
      },
      {
        header: 'Buy Price',
        accessorKey: 'buy_price',
        cell: ({ getValue }) => (
          <span className="text-osrs-red">{formatExactGP(getValue())}</span>
        ),
      },
      {
        header: 'Sell Price',
        accessorKey: 'sell_price',
        cell: ({ getValue }) => (
          <span className="text-osrs-green">{formatExactGP(getValue())}</span>
        ),
      },
      {
        header: 'Profit',
        accessorKey: 'profit',
        cell: ({ getValue }) => (
          <span className="text-osrs-gold font-bold">{formatGP(getValue())}</span>
        ),
      },
      {
        header: 'Limit Profit',
        accessorKey: 'limit_profit',
        cell: ({ getValue }) => (
          <span className="text-blue-400 font-bold">{formatGP(getValue())}</span>
        ),
      },
      {
        header: 'ROI %',
        accessorKey: 'roi',
        cell: ({ getValue }) => {
          const roi = getValue();
          const color = roi >= 10 ? 'text-osrs-green' : 
                       roi >= 5 ? 'text-yellow-400' : 'text-gray-400';
          return <span className={color}>{formatPercent(roi)}</span>;
        },
      },
      {
        header: 'Score',
        accessorKey: 'score',
        cell: ({ getValue }) => {
          const score = getValue();
          const color = score >= 70 ? 'text-osrs-green' :
                       score >= 45 ? 'text-yellow-400' :
                       score >= 25 ? 'text-orange-400' : 'text-gray-400';
          return <span className={`font-bold ${color}`}>{score ?? '—'}</span>;
        },
      },
      {
        header: 'Risk-Adj Score',
        accessorKey: 'risk_adjusted_score',
        cell: ({ getValue }) => {
          const val = getValue();
          if (val == null) return <span className="text-gray-500">—</span>;
          const color = val >= 70 ? 'text-osrs-green' :
                        val >= 45 ? 'text-yellow-400' :
                        val >= 25 ? 'text-orange-400' : 'text-gray-400';
          return <span className={`font-bold ${color}`}>{val.toFixed(1)}</span>;
        },
      },
      {
        header: 'Risk Profile',
        accessorKey: 'crash_risk_score',
        cell: ({ getValue }) => {
          const val = getValue();
          if (val == null) return <span className="text-gray-500">—</span>;
          const color = val < 35 ? 'text-osrs-green' :
                        val <= 70 ? 'text-yellow-400' : 'text-osrs-red';
          const label = val < 35 ? 'Low' :
                        val <= 70 ? 'Medium' : 'High';
          return <span className={`font-bold ${color}`} title={`Crash Risk Score: ${val.toFixed(1)}`}>{label} ({val.toFixed(0)})</span>;
        },
      },
      {
        header: () => (
          <span title="Hourly trading volume (high + low price volumes)">
            Volume
          </span>
        ),
        accessorKey: 'volume',
        cell: ({ getValue }) => {
          const volume = getValue();
          const indicator = getVolumeIndicator(volume);
          return (
            <div className="flex items-center gap-2">
              <span>{indicator.emoji}</span>
              <span className={indicator.color}>{volume?.toLocaleString() || 'N/A'}</span>
            </div>
          );
        },
      },
      {
        header: 'GE Limit',
        accessorKey: 'ge_limit',
        cell: ({ getValue }) => getValue()?.toLocaleString() || 'N/A',
      },
      {
        header: 'Action',
        id: 'actions',
        cell: ({ row }) => (
          <button
            className="btn btn-primary text-sm py-1 px-3"
            onClick={(e) => {
              e.stopPropagation();
              onSelectFlip(row.original);
            }}
          >
            Buy
          </button>
        ),
      },
      {
        header: '',
        id: 'expand',
        cell: ({ row }) => (
          <button
            className="text-gray-400 hover:text-white transition-colors px-2"
            onClick={(e) => {
              e.stopPropagation();
              toggleRow(row.id);
            }}
          >
            <span className={`inline-block transition-transform duration-200 text-sm ${expandedRows[row.id] ? 'rotate-90' : ''}`}>
              ›
            </span>
          </button>
        ),
      },
    ],
    [onSelectFlip, onShowDetail, expandedRows, toggleRow]
  );

  const table = useReactTable({
    data: flips || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const columnCount = columns.length;

  return (
    <div className="card overflow-x-auto hidden md:block">
      <table className="w-full">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-gray-700">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="text-left p-3 font-semibold text-osrs-gold"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => {
            const item = row.original;
            const isExpanded = expandedRows[row.id];

            return (
              <React.Fragment key={row.id}>
                <tr
                  className="border-b border-gray-700 hover:bg-gray-750 transition-colors cursor-pointer"
                  onClick={() => toggleRow(row.id)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
                {isExpanded && (
                  <tr className="bg-gray-750">
                    <td colSpan={columnCount} className="p-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Max Qty (Cash)</p>
                          <p className="font-medium">{item.max_qty?.toLocaleString() || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Your Profit</p>
                          <p className="font-bold text-osrs-green">{formatGP(item.your_profit)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Profit at Limit</p>
                          <p className="font-bold text-blue-400">{formatGP(item.profit_at_limit)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Member Status</p>
                          <p className="font-medium">
                            {item.members
                              ? <span className="text-yellow-400">⭐ Members</span>
                              : <span className="text-gray-300">F2P</span>
                            }
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">GE Tax</p>
                          <p className="font-medium text-osrs-red">
                            {item.sell_price > 50
                              ? formatGP(Math.floor(item.sell_price * 0.02))
                              : '0 gp'
                            }
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Score</p>
                          <p className={`font-bold ${
                            item.score >= 70 ? 'text-osrs-green' :
                            item.score >= 45 ? 'text-yellow-400' :
                            item.score >= 25 ? 'text-orange-400' : 'text-gray-400'
                          }`}>{item.score ?? '—'} / 100</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Risk-Adj Score</p>
                          <p className={`font-bold ${
                            item.risk_adjusted_score >= 70 ? 'text-osrs-green' :
                            item.risk_adjusted_score >= 45 ? 'text-yellow-400' :
                            item.risk_adjusted_score >= 25 ? 'text-orange-400' : 'text-gray-400'
                          }`}>{item.risk_adjusted_score != null ? `${item.risk_adjusted_score.toFixed(1)} / 100` : '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Crash Risk Score</p>
                          <p className={`font-bold ${
                            item.crash_risk_score == null ? 'text-gray-500' :
                            item.crash_risk_score < 35 ? 'text-osrs-green' :
                            item.crash_risk_score <= 70 ? 'text-yellow-400' : 'text-osrs-red'
                          }`}>{item.crash_risk_score != null ? `${item.crash_risk_score.toFixed(0)} / 100` : '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Max Drawdown (30d)</p>
                          <p className="font-medium text-osrs-red">
                            {item.max_drawdown_30d != null ? `${item.max_drawdown_30d.toFixed(1)}%` : '—'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Price Percentile (30d)</p>
                          <p className="font-medium">
                            {item.price_percentile_30d != null ? `${item.price_percentile_30d.toFixed(1)}%` : '—'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Risk-to-Reward</p>
                          <p className={`font-medium ${
                            item.risk_to_reward_ratio == null ? 'text-gray-500' :
                            item.risk_to_reward_ratio > 3 ? 'text-osrs-red' :
                            item.risk_to_reward_ratio > 1.5 ? 'text-yellow-400' : 'text-osrs-green'
                          }`}>{item.risk_to_reward_ratio != null ? `${item.risk_to_reward_ratio.toFixed(2)}x` : '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Erebus Score</p>
                          <p className={`font-bold ${
                            item.secondary_score == null ? 'text-gray-500' :
                            item.secondary_score >= 50 ? 'text-purple-400' :
                            item.secondary_score >= 20 ? 'text-osrs-green' :
                            item.secondary_score >= 5 ? 'text-yellow-400' : 'text-gray-400'
                          }`}>{item.secondary_score ?? '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Data Quality</p>
                          <p className={`font-bold ${
                            item.quality_score == null ? 'text-gray-500' :
                            item.quality_score >= 80 ? 'text-osrs-green' :
                            item.quality_score >= 50 ? 'text-yellow-400' : 'text-osrs-red'
                          }`}>
                            {item.quality_score != null ? `${item.quality_score.toFixed(0)} / 100` : '—'}
                            {item.quality_flags?.length > 0 && (
                              <span className="text-xs block text-orange-400 mt-1">
                                ⚠ {item.quality_flags[0]}
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
});

export default FlipTable;
