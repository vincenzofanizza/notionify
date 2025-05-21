import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FilePlus, Loader2, AlertCircle, CircleCheck, CircleX } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const Popup: React.FC = () => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isChecking, setIsChecking] = useState<boolean>(true);
  const [guidance, setGuidance] = useState<string>('');
  const [response, setResponse] = useState<{message: string, link?: string} | null>(null);
  const [existingPage, setExistingPage] = useState<{title: string, page_url: string} | null>(null);
  const [currentUrl, setCurrentUrl] = useState<string>('');

  // Check if the URL already exists in Notion when the component mounts
  useEffect(() => {
    const checkExistingPage = async () => {
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        const activeTab = tabs[0];
        const url = activeTab.url || '';
        setCurrentUrl(url);
        
        setIsChecking(true);
        console.log(`Checking URL: ${url}`);
        
        const response = await fetch(
          `https://get-notion-page-ny7vkn2pgq-ew.a.run.app?url=${encodeURIComponent(url)}`
        );

        // Parse JSON only if the response is successful
        if (response.ok) {
            const data = await response.json();
            
            if (data && data.title && data.page_url) {
              setExistingPage({
                title: data.title,
                page_url: data.page_url
              });
            } else {
              console.log('Data missing required fields:', data);
            }
        }
      } catch (error) {
        console.error('Error checking for existing page:', error);
      } finally {
        setIsChecking(false);
      }
    };
    
    checkExistingPage();
  }, []);

  const handleAddToNotion = async () => {
    setIsLoading(true);
    setResponse(null);
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000);

      const response = await fetch(
        `https://create-notion-page-ny7vkn2pgq-ew.a.run.app?url=${encodeURIComponent(currentUrl)}&guidance=${encodeURIComponent(guidance)}`,
        { signal: controller.signal }
      );
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }
      
      const result = await response.json();
      console.log('Success:', result);
      setResponse({ 
        message: `New page created: ${result.title}`, 
        link: result.page_url 
      });
    } catch (error) {
      console.error(error);
      setResponse({ message: `There was an error` });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-2 w-[400px] font-inter bg-[#0A2342]">
      <Card className="bg-cream border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-center text-3xl font-medium text-[#0A2342]">notionify</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2 items-end">
            <Textarea 
              value={guidance}
              onChange={(e) => setGuidance(e.target.value)}
              placeholder="What should the report focus on?"
              disabled={isLoading || isChecking}
              className="min-h-[80px] text-sm flex-1 bg-white/80 border-slate-200 placeholder:text-slate-400 text-slate-700 focus-visible:ring-1 focus-visible:ring-[#0A2342] focus-visible:border-[#0A2342] resize-handle-lg"
            />            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    onClick={handleAddToNotion}
                    disabled={isLoading || isChecking}
                    size="icon"
                    className="flex-shrink-0 bg-[#0A2342] hover:bg-[#0A2342]/90 text-white"
                  >
                    {isLoading ? <Loader2 size={20} className="animate-spin" /> : <FilePlus size={20} />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Add to Notion</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          
          {isChecking ? (
            <div className="flex items-center justify-center py-1 text-slate-600">
              <Loader2 size={16} className="mr-2 animate-spin" />
              <span className="text-xs mt-[1px]">Checking database...</span>
            </div>
          ) : existingPage && (
            <div className="flex items-start text-amber-600 text-xs">
              <AlertCircle size={16} className="mr-1 flex-shrink-0" />
              <span className="mt-[1px]">
                This page already exists in Notion as{" "}
                <a 
                  href={existingPage.page_url} 
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-amber-700 hover:underline underline"
                >
                  "{existingPage.title}"
                </a>
              </span>
            </div>
          )}
          
          {response && (
            <div className={`flex items-start text-xs ${
              response.link 
                ? 'text-emerald-600' 
                : 'text-red-600'
            }`}>
              {response.link ? (
                <CircleCheck size={16} className="mr-1 flex-shrink-0" />
              ) : (
                <CircleX size={16} className="mr-1 flex-shrink-0" />
              )}
              <span className="mt-[1px]">
                {response.link ? (
                  <>
                    New page created:{" "}
                    <a 
                      href={response.link} 
                      target="_blank" 
                      rel="noreferrer"
                      className="font-medium text-emerald-700 hover:underline underline"
                    >
                      "{response.message.replace('New page created: ', '')}"
                    </a>
                  </>
                ) : (
                  <span className="font-medium text-red-700">
                    {response.message}
                  </span>
                )}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
      <div className="text-xs mt-2 text-white pb-1 pr-2 text-right italic">v0.1.0 (alpha)</div>
    </div>
  );
};

export default Popup; 