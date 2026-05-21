import React, { useState, useMemo, useCallback } from 'react';
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import { formatGP, formatExactGP, formatPercent, getVolumeIndicator } from '../utils/formatters';

const LongTermFlipTable = React.memo(function LongTermFlipTable({ flips, onSelectFlip, onShowDetail }) {
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
          const scoreColor = item.long_term_score >= 70 ? 'text-osrs-green' :
                            item.long_term_score >= 45 ? 'text-luxury-gold' :
                            item.long_term_score >= 25 ? 'text-orange-400' : 'text-gray-400';

          return (
            <div key={item.id} className="card p-0 overflow-hidden">
              {/* Collapsed: Name + Score + Chevron */}
              <button
                className="w-full flex items-center justify-between p-4 text-left"
                onClick={() => toggleRow(idx)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span
                    className="font-semibold font-cinzel text-luxury-gold truncate cursor-pointer hover:text-luxury-goldBright bg-transparent border-0 p-0 transition-colors"
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
                  </span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`font-bold font-outfit ${scoreColor}`}>{item.long_term_score ?? '—'}</span>
                  <span className={`text-luxury-purpleLight/60 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}>
                    ›
                  </span>
                </div>
              </button>

              {/* Expanded: All data */}
              {isExpanded && (
                <div className="border-t border-luxury-border/30 px-4 pb-4">
                  {/* Key metrics */}
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    <MobileField label="Buy Price" value={formatExactGP(item.buy_price)} color="text-osrs-red" />
                    <MobileField label="Exp. Sell (7d)" value={formatExactGP(item.expected_sell_price)} color="text-osrs-green" />
                    <MobileField label="Exp. Profit" value={formatGP(item.expected_profit_7d)} color="text-luxury-gold" />
                    <MobileField label="Exp. ROI" value={formatPercent(item.expected_roi_7d)} color={
                      item.expected_roi_7d >= 10 ? 'text-osrs-green' : item.expected_roi_7d >= 5 ? 'text-luxury-gold' : 'text-gray-400'
                    } />
                    <MobileField label="Limit Profit" value={formatGP(item.limit_profit)} color="text-luxury-purpleLight" />
                    <MobileField label="Volume" value={
                      (() => { const v = getVolumeIndicator(item.volume); return `${v.emoji} ${item.volume?.toLocaleString() || 'N/A'}`; })()
                    } />
                    <MobileField label="GE Limit" value={item.ge_limit?.toLocaleString() || 'N/A'} />
                    <MobileField label="Long Term Score" value={`${item.long_term_score ?? '—'} / 100`} color={scoreColor} />
                    <MobileField label="Your Profit" value={formatGP(item.your_profit)} color="text-osrs-green" />
                    <MobileField label="Max Qty" value={item.max_qty?.toLocaleString() || 'N/A'} />
                    <MobileField label="Members" value={item.members ? '⭐ Members' : 'F2P'} />
                    <MobileField label="GE Tax" value={
                      item.sell_price > 50 ? formatGP(Math.floor(item.sell_price * 0.02)) : '0 gp'
                    } color="text-osrs-red" />
                    {item.secondary_score != null && (
                      <MobileField label="Erebus Score" value={item.secondary_score} color={
                        item.secondary_score >= 50 ? 'text-luxury-purple' :
                        item.secondary_score >= 20 ? 'text-osrs-green' :
                        item.secondary_score >= 5 ? 'text-luxury-gold' : 'text-gray-400'
                      } />
                    )}
                    <div className="col-span-2">
                      <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-0.5">Data Quality</p>
                      <p className={`font-bold font-outfit ${
                        item.quality_score == null ? 'text-gray-500' :
                        item.quality_score >= 80 ? 'text-osrs-green' :
                        item.quality_score >= 50 ? 'text-luxury-gold' : 'text-osrs-red'
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
                  <div className="mt-3 text-xs text-gray-500 font-outfit space-y-1">
                    <p>Buy: {item.buy_price?.toLocaleString()} gp · Exp. Sell: {item.expected_sell_price?.toLocaleString()} gp · Exp. Profit: {item.expected_profit_7d?.toLocaleString()} gp</p>
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
      <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-0.5">{label}</p>
      <p className={`font-medium text-sm font-outfit ${color}`}>{value}</p>
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
            className="font-semibold font-cinzel text-luxury-gold hover:text-luxury-goldBright text-left transition-colors"
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
          <span className="text-osrs-red font-outfit">{formatExactGP(getValue())}</span>
        ),
      },
      {
        header: 'Expected Sell (7d)',
        accessorKey: 'expected_sell_price',
        cell: ({ getValue }) => (
          <span className="text-osrs-green font-outfit">{formatExactGP(getValue())}</span>
        ),
      },
      {
        header: 'Expected Profit',
        accessorKey: 'expected_profit_7d',
        cell: ({ getValue }) => (
          <span className="text-luxury-gold font-bold font-outfit">{formatGP(getValue())}</span>
        ),
      },
      {
        header: 'Limit Profit',
        accessorKey: 'limit_profit',
        cell: ({ getValue }) => (
          <span className="text-luxury-purpleLight font-bold font-outfit">{formatGP(getValue())}</span>
        ),
      },
      {
        header: 'Expected ROI %',
        accessorKey: 'expected_roi_7d',
        cell: ({ getValue }) => {
          const roi = getValue();
          const color = roi >= 10 ? 'text-osrs-green' : 
                       roi >= 5 ? 'text-luxury-gold' : 'text-gray-400';
          return <span className={`font-outfit ${color}`}>{formatPercent(roi)}</span>;
        },
      },
      {
        header: 'Long Term Score',
        accessorKey: 'long_term_score',
        cell: ({ getValue }) => {
          const score = getValue();
          const color = score >= 70 ? 'text-osrs-green' :
                       score >= 45 ? 'text-luxury-gold' :
                       score >= 25 ? 'text-orange-400' : 'text-gray-400';
          return <span className={`font-bold font-outfit ${color}`}>{score ?? '—'}</span>;
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
            <div className="flex items-center gap-2 font-outfit">
              <span>{indicator.emoji}</span>
              <span className={indicator.color}>{volume?.toLocaleString() || 'N/A'}</span>
            </div>
          );
        },
      },
      {
        header: 'GE Limit',
        accessorKey: 'ge_limit',
        cell: ({ getValue }) => (
          <span className="font-outfit">{getValue()?.toLocaleString() || 'N/A'}</span>
        ),
      },
      {
        header: 'Action',
        id: 'actions',
        cell: ({ row }) => (
          <button
            className="btn btn-primary text-xs py-1.5 px-3"
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
            className="text-luxury-purpleLight/60 hover:text-luxury-goldBright transition-colors px-2"
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
    <div className="luxury-table-container hidden md:block">
      <table className="luxury-table">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
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
                  className="cursor-pointer"
                  onClick={() => toggleRow(row.id)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
                {isExpanded && (
                  <tr className="expanded-details">
                    <td colSpan={columnCount} className="p-5">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Max Qty (Cash)</p>
                          <p className="font-medium font-outfit text-sm text-slate-200">{item.max_qty?.toLocaleString() || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Your Profit</p>
                          <p className="font-bold font-outfit text-sm text-osrs-green">{formatGP(item.your_profit)}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Profit at Limit</p>
                          <p className="font-bold font-outfit text-sm text-luxury-purpleLight">{formatGP(item.profit_at_limit)}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Member Status</p>
                          <p className="font-medium font-outfit text-sm">
                            {item.members
                              ? <span className="text-luxury-gold">⭐ Members</span>
                              : <span className="text-slate-300">F2P</span>
                            }
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">GE Tax</p>
                          <p className="font-medium font-outfit text-sm text-osrs-red">
                            {item.sell_price > 50
                              ? formatGP(Math.floor(item.sell_price * 0.02))
                              : '0 gp'
                            }
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Long Term Score</p>
                          <p className={`font-bold font-outfit text-sm ${
                            item.long_term_score >= 70 ? 'text-osrs-green' :
                            item.long_term_score >= 45 ? 'text-luxury-gold' :
                            item.long_term_score >= 25 ? 'text-orange-400' : 'text-gray-400'
                          }`}>{item.long_term_score ?? '—'} / 100</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Erebus Score</p>
                          <p className={`font-bold font-outfit text-sm ${
                            item.secondary_score == null ? 'text-gray-500' :
                            item.secondary_score >= 50 ? 'text-luxury-purple' :
                            item.secondary_score >= 20 ? 'text-osrs-green' :
                            item.secondary_score >= 5 ? 'text-luxury-gold' : 'text-gray-400'
                          }`}>{item.secondary_score ?? '—'}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-luxury-purpleLight/60 font-semibold mb-1">Data Quality</p>
                          <p className={`font-bold font-outfit text-sm ${
                            item.quality_score == null ? 'text-gray-500' :
                            item.quality_score >= 80 ? 'text-osrs-green' :
                            item.quality_score >= 50 ? 'text-luxury-gold' : 'text-osrs-red'
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

export default LongTermFlipTable;
